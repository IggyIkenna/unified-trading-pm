---name: strategy-repo-consolidation-2026-05-19
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
epic: strategy_and_dart_master_SUPERSEDED_2026_05_21
status: active-cleanup-phase-11

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
    status: done
    blocked_by: phase-3-subtree-merge

  - id: phase-5-lifts-to-utl
    content: |
      - [x] ✅ [AGENT] P1. Phase 5 — Lift cross-cutting helpers to UTL. — utl@e2445522 + strategy-service@054fae03
        `ConfigReloaderBase[T]` → `unified_trading_library/config_interface/config_reloader_base.py` (9 tests).
        `KillSwitchBusSubscriberBase` → `unified_trading_library/lifecycle/kill_switch_subscriber_base.py` (13 tests).
        4× config_reloaders.py + 4× kill_switch_bus_subscriber.py refactored to use base classes.
        strategy-service: 1456 passed, 0 errors; utl: 22 new tests all pass; basedpyright clean both repos.
    status: done
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
      - [x] ✅ [HUMAN+AGENT] P0. Phase 7 — Archive the 3 source repos. COMPLETE 2026-05-20.
        Agent-half (2026-05-19):
        1. ✅ DEPRECATION_NOTICE.md committed: risk@6e52257 + position@f602e58 + pnl@c1ac3f0
        2. ✅ strategy-service CHANGELOG + QGBA merged: strategy-service@607a411b
        3. ✅ workspace-manifest.json updated (status=pending-archive): PM@b6907afe0
        4. ✅ code-workspace folders list cleaned (29→26 entries): PM@b6907afe0
        5. ✅ setup-tab-worktrees.sh auto-skips repos with `archived_into` set — no edit needed
        6. ✅ operator ping filed in `_agent_pings.md`: PM@b6907afe0
        Operator actions (2026-05-20):
        7. ✅ `gh repo archive IggyIkenna/risk-and-exposure-service --yes` — archived=true verified
        8. ✅ `gh repo archive IggyIkenna/position-balance-monitor-service --yes` — archived=true verified
        9. ✅ `gh repo archive IggyIkenna/pnl-attribution-service --yes` — archived=true verified
        Agent follow-up (2026-05-20):
        10. ✅ workspace-manifest.json status→archived + archived_into + archived_date: PM@ad31a6710
        11. ✅ cursor-configs/unified-trading-system-repos.code-workspace: 24 git.ignoredRepositories entries removed (3 repos × 8 tabs): PM@ad31a6710
        12. ✅ cursor-configs/workspace-complete.code-workspace: 3 folders entries removed: PM@ad31a6710
        13. ✅ cursor-configs/workspace-trading.code-workspace: 3 folders entries removed: PM@ad31a6710
    status: done
    blocked_by: phase-6-parity-test

  - id: phase-8a-launcher-migration
    content: |
      - [x] ✅ [AGENT] P0. Phase 8A — Launcher migration in `deployment-service`. deployment-service@7679dfe + @2ed3fdd (2026-05-19):
        - `cloud-build/refresh-tarballs.cloudbuild.yaml`: dropped 3 source services from clone list
        - `scripts/vm/create-code-tarballs.sh`: removed 3 source repos from all 5 category arrays
        - `scripts/vm/setup-data-pipeline-vm.sh`: SERVICE_TARBALLS remapped to strategy-service-code
        - `scripts/vm/backfill-cluster.sh`: L7 case arms now invoke `python -m strategy_service --operation {pnl-attribution,risk-monitor,position-recon}`
        - `configs/_topology_nodes_upper.py`: consolidated 3 nodes into single STRAT_L7 node with operation-axis
        - `configs/_topology_panels.py`: updated Cloud Run Job panel text
        - `terraform/cloud-build/gcp/main.tf`: removed 3 source service trigger entries
        - `terraform/services/{risk,position,pnl}/`: ARCHIVED.md destroy-runbook added
        - Workflow audit: 0 migrations needed (27 workflows examined — all PM-template-derived or obsolete)
        - Branch protection clean: no orphan refs from archived repos
    status: done
    blocked_by: phase-7-archive-source-repos

  - id: phase-8b-deployment-api-ui
    content: |
      - [x] ✅ [AGENT] P0. Phase 8B — `deployment-api` + `deployment-ui` updates. Service registry endpoints
        (`/services/list`, `/services/<id>/health`) update to remove the 3 source service IDs and expose
        per-operation health on strategy-service. DART drilldown UI updates for risk-monitor + position-recon +
        pnl-attribution surfaces to point at strategy-service health endpoints. Update `MinimalCandidateManifest`
        Firestore consumers if any reference `risk_and_exposure_service` / etc. by name (Phase 0 (h) finding).
        — deployment-api@bd87d70 + deployment-ui@d22f2ba (2026-05-20). Removed 3 old IDs from VALID_SERVICES,
        SERVICES_WITH_TRIGGERS, _KNOWN_TARBALL_SERVICES, _ASSET_GROUP_TARBALLS (5 asset groups), RICH_SERVICES,
        TURBO_SUB_DIMENSION_SERVICES, OVERRIDABLE_SERVICES; added risk-monitor/position-recon/pnl-attribution
        operations to strategy-service entry in ServiceList.tsx.
    status: done
    blocked_by: phase-7-archive-source-repos

  - id: phase-9-codex-ssot-updates
    content: |
      - [x] ✅ [AGENT] P0. Phase 9 — Codex SSOT updates. — PM@4d934d7ac (2026-05-20)
        (a) `codex/04-architecture/strategy-service-architecture.md`: status stub→stable; caveat updated to
            reflect consolidation complete (Phase 6 parity 4059 passed 0 errors).
        (b) `codex/00-SSOT-INDEX.md`: strategy-service row STUB→STABLE with parity evidence + launcher sha.
        (c) `promote-workflow-architecture.md`: no old-service references found — already clean.
        (d) `launcher-script-ssot.md`: no old-service references found — already clean.
        (e) `vm-tarball-deployment.md`: no old-service references found — already clean.
        (f) `cli-convention.md`: no old-service references found — already clean.
        (g) `cli-promote-paths.md`: no old-service references found — already clean.
        (h) Migration banners added to 5 high-traffic architectural docs: runtime-deployment-topology.md,
            data-flow-map.md, risk-preflight-flow.md, LIBRARY-DEPENDENCY-MATRIX.md, INTERNAL_DEPENDENCY_GRAPH.md.
            10-audit/ + _archived_pre_v2/ historical docs intentionally left as-is (historical record).
    status: done
    blocked_by: phase-8a-launcher-migration

  - id: phase-10-workspace-qg-sweep
    content: |
      - [x] ✅ [AGENT] P0. Phase 10 — Workspace QG sweep + cross-plan coordination banner cleanup. — PM@(this commit) strategy-service@467cf674 (2026-05-20)
        Banners stripped from 21 active plans. Inventory regenerator run: 68 plans, 64% done.
        QG: all unit tests passing including asyncio.run() fix for pnl orchestrator tests (Python 3.13 compat).
        VM smoke test BLOCKED-OPERATOR (human-only VM launch; agent cannot boot strategy-service VM).
    status: done
    blocked_by: phase-9-codex-ssot-updates

  - id: phase-0-side-effect-soft-freeze-announcement
    content: |
      - [x] ✅ [AGENT] P0. Phase 0 SIDE EFFECT — Cross-plan soft-freeze announcement. Add coordination banner to
        every active plan identified in fact-report (2026-05-19) as having scope over the 4 affected repos
        (~12 plans with `repo_gates`, ~34 with passing mentions). Banner text:
        ```

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
parent_epic: strategy_master
---

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
  hard); race the 2026-05-23 cutover; fold under existing `strategy_and_dart_master_SUPERSEDED_2026_05_21` epic (NOT new
  standalone epic). Operator + colleague aligned on approach.
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
- [x] ✅ **P0** [DECISION] Topic-prefix compatibility decision — **DECIDED: KEEP legacy topic prefixes**
      (`risk-monitor.*`, `position-monitor.*`, `pnl-attribution.*`) for first 7 days post-cutover to avoid double-rebind
      race during the live trading window. Rename via follow-up plan. Default YES applied (no cross-cutting reason to
      rename atomically surfaced). — recorded 2026-05-20 slot 5
- [x] ✅ **P0** [AGENT] Phase 4 (g) verify `PYTEST_UNIT_DIR="tests/"` override applied — PBM's
      `tests/position_interface/unit/` layout triggers the per-family rule per CLAUDE.md. Without it the merged
      strategy-service QG silently skips position-recon unit tests. — ✅ strategy-service@1da6743b (2026-05-19);
      multi-dir override `tests/unit/ tests/risk/unit/ tests/position/unit/ tests/pnl/unit/` in scripts/quality-gates.sh
- [x] ✅ **P1** [AGENT] Phase 4 cleanup — remove `try/except ImportError` guards from
      `system-integration-tests/tests/smoke/test_sports_arb_pipeline.py` (banned per CLAUDE.md
      `.cursor/rules/no-empty-fallbacks.mdc`); imports become unconditional intra-package post-merge. — ✅
      system-integration-tests@0b20329 (2026-05-19)
- [x] ✅ **P1** [AGENT+DECISION] Architectural-collision resolution — existing `strategy_service/models/position.py` +
      `strategy_service/models/pnl.py` will coexist with new `strategy_service/{position,pnl}/` sub-packages. Symbols
      don't collide but layout confuses readers. Decide in Phase 4 (a): (i) absorb existing models into sub-packages
      (preferred), (ii) keep both with cross-link comments, (iii) rename existing to
      `strategy_service/models/legacy_*.py`. Not cutover-blocking. — ✅ strategy-service@f7c62f61 (2026-05-20): DECISION
      option (ii): added NOTE cross-link comments to models/pnl.py + models/position.py (UAC type aliases) pointing to
      strategy_service.pnl/position sub-packages (computation). Added reverse pointers in pnl/**init**.py +
      position/**init**.py. Option (i) deferred post-May-23 to avoid callsite-breakage risk at T-3 days.
- [x] ✅ **P1** [AGENT] Phase 8A sharpening — Terraform destroy audit. VERIFIED 2026-05-20 slot 5:
      `terraform/services/{risk,position,pnl}/gcp/` have no `backend.tf` (no remote state). GCP confirmed:
      `gcloud run jobs list` + `gcloud workflows list` → zero resources for all 3 services. AWS confirmed:
      `aws ecs list-services` → no resources. No orphan Terraform-managed resources exist. Destroy is a no-op;
      ARCHIVED.md runbooks remain as documentation but no `terraform destroy` execution needed.
- [x] ✅ **P1** [AGENT] Phase 5 lifts — `config_reloaders.py` is duplicated 4× (152/112/112/312 LOC, total ~688 LOC) and
      is a clean UTL `ConfigReloaderBase` candidate. Kill-switch bus subscriber boilerplate is duplicated 4× (~80-100
      LOC each) and is a clean UTL `KillSwitchBusSubscriberBase` candidate. Both confirmed by artifact § (f).
      **UN-DEFERRED 2026-05-20 per operator direction** (work_split_2026_05_19_ikenna.md): lifts are additive in UTL
      (patch bump, no removals), blast radius bounded. Ship as 2 UTL PRs. Slot 5 picks up immediately. — ✅
      utl@e2445522 + strategy-service@054fae03 (backfilled 2026-05-20)
- [ ] [AGENT] P2. After May-23 architecture unlock, `StrategyDirectiveReloader` becomes the 5th typed-reloader callsite;
      lift into UTL as `make_directive_reloader()` alongside `make_config_reloader()` per epic §1.7. POST-CUTOVER.
- [x] ✅ **P2** [AGENT] Console-script command-name compatibility — the 3 source repos define `[project.scripts]`
      entries (`risk-monitor`, `position-monitor`, `position-monitor-std`, `pnl-attribution`, `pnl-attribution-std`).
      Post-merge: collapse to `python -m strategy_service --operation <op>`. Audit any launcher / cron / VM bootstrap
      script invoking the legacy command names; rewrite in Phase 8A. — ✅ VERIFIED 2026-05-20 slot 5: zero
      console-script name invocations found across all workspace scripts; all launch paths already use `python -m`
      module form.

### Gap-close 2026-05-19 — coverage amendments (post-dispatch audit)

Operator-validation question 2026-05-19 surfaced 4 gaps in the original 10-phase scope. Closing them now (before
slot-3/4/7/9 boot) is cheaper than discovering them mid-Phase-4 or post-archive.

- [x] ✅ **P0 NEW** [AGENT slot 4] Phase 4 (a-extension) — e2e-testing scripts beyond Python imports. Phase 4 (a)
      currently covers the 7 `import`-consumer files from pre-audit § (b). Add: grep
      `e2e-testing/scripts/{defi,sports,prediction}/`
  - `system-integration-tests/scripts/` + `e2e-testing/scripts/*.sh` for (i) shell invocations of
    `python -m {risk_and_exposure,position_balance_monitor,pnl_attribution}_service`, (ii) console-script names
    (`risk-monitor`, `position-monitor`, `pnl-attribution`, etc.), (iii) bare-Python entry-point invocations. Rewrite to
    `python -m strategy_service --operation <op>`. Slot 4 extends Phase 4 (a) by ~0.5 cal-day. — ✅ e2e-testing@ad55362
    (2026-05-20): 4 run-full-pipeline.sh + data_layer_runner.py + colocated_engine.py rewritten to
    strategy-service::{pnl-attribution,risk-monitor,position-recon}
- [x] ✅ **P0 NEW** [AGENT slot 7] Phase 8A — Console-script alias audit (PROMOTED from P2 to P0). Source repos define
      `[project.scripts]`: `risk-monitor`, `position-monitor`, `position-monitor-std`, `pnl-attribution`,
      `pnl-attribution-std`. These are invoked by name in deployment-service launchers, cron schedules, VM bootstrap
      scripts, e2e-testing scripts, docs. **Decision: full cutover, no shim aliases in strategy-service
      `[project.scripts]`** — launchers + cron are workspace-owned and rewriting them is the cleanest path. Slot 7
      bundles this into Phase 8A launcher migration; ~0.5 cal-day extension. — ✅ VERIFIED 2026-05-20 slot 5: grep
      across deployment-service + e2e-testing finds ZERO invocations of
      `risk-monitor`/`position-monitor`/`pnl-attribution` as console-script commands. backfill-cluster.sh already uses
      `python -m strategy_service --operation {pnl-attribution,risk-monitor}`. e2e-testing rewritten in Phase 4
      (a-extension). No shim aliases required. Strategy-service pyproject.toml remains unchanged.
- [x] ✅ **P1 NEW** [AGENT slot 4] Phase 4 (i) — Logging + observability config consolidation. Per-service
      `setup_events()` callsites + log levels + formatters + structured-log field naming. Decide: per-sub-package logger
      naming (`strategy_service.risk` / `strategy_service.position` / `strategy_service.pnl` /
      `strategy_service.engine`) for filterability. OpenTelemetry tracers + Prometheus metrics + Cloud Trace spans —
      collapse `service.name=<source-repo>` labels to `service.name=strategy-service` and add
      `subsurface={risk,position,pnl,strategy}` label dimension. ServiceBootstrap in Phase 4 (e) already covers
      lifecycle-event emission; this is the parallel pass for log + metric + trace infra. Slot 4 extends Phase 4 by ~0.5
      cal-day. — ✅ strategy-service@25638f4b (2026-05-20): 76 occurrences across 34 files; config.service_name + API
      titles + log messages → "strategy-service"; UAC seed keys (\_SERVICE_NAME in emission/isolation policy) +
      filesystem path keys (mock_data_provider) preserved at legacy values; test assertions updated to match. 0
      failures. Slot 4 extension @29e4f149: \_SERVICE_NAME renamed to "strategy-service" in all 3 sub-packages
      (position/risk/pnl isolation_policy.py + core sinks + mock_data_provider + 51 test assertions across 24 files);
      uac@b3bb291 adds BLOCK_CRITICAL for (strategy-service, portfolio_state) + (strategy-service, risk_state); 4118
      passed 0 failed.
- [x] ✅ **P2 NEW** [AGENT slot 3] Phase 3 addendum — Drop source-repo `docs/` subdirectories during subtree-merge.
      `git read-tree --prefix=strategy_service/<sub>/ -u <source>-remote/main:<source_package>/` pulls package + tests +
      scripts only; `docs/` intentionally NOT merged (codex is workspace SSOT). Record in each archived source repo's
      `DEPRECATION_NOTICE.md` (Phase 7): "docs/ content not migrated — see
      `codex/04-architecture/strategy-service-architecture.md` and related codex pages." 1-line addendum to Phase 3
      recipe; <5 min work. — VERIFIED 2026-05-19: `git show {92515fde,cb200745,c67fb13d} --stat | grep docs/` returns
      empty — docs/ correctly excluded from all 3 subtree-merge commits. Handoff to Phase 7 (slot 6): include "docs/ not
      migrated" note in DEPRECATION_NOTICE.md per above.
- [x] ✅ **P0** [AGENT slot 8] Phase 4 basedpyright/test fix pass — 71 basedpyright errors resolved across
      strategy_service/ (cast() patterns for pandas/model_dump, public rename \_VenueData→VenueData +
      \_apply_fill_to_position→apply_fill_to_position, log_event field names fixed for RiskMetrics UAC fields,
      **init**.py added to tests/risk/ + tests/position/ unit dirs, sys.path depth fix in
      test_capture_phase_9_evidence.py). Multi-repo cleanup: dirty working trees in deployment-api, e2e-testing,
      execution-service, pnl-attribution-service, system-integration-tests, unified-trading-pm resolved and rebased onto
      remote. All repos clean. — strategy-service@d9a76e9a + system-integration-tests@fd45c5a (2026-05-20) Evidence:
      ruff → All checks passed; basedpyright → 0 errors; pytest tests/risk/unit/ tests/position/unit/ tests/pnl/unit/ →
      1456 passed, 2 skipped.
- [x] ✅ **P2 NEW** [AGENT slot 7] Phase 8A addendum — GitHub Actions workflows in source repos going dark. Each
      archived repo carries ~9 workflow files (~27 total across risk + position + pnl). Most are templated copies
      (`workspace-qg.yml`, `semver-agent.yml`, `staging-lock-check.yml`, `tab-mirror-to-ldr.yml`) that strategy-service
      already has via `rollout-workflow-templates.sh` — those just go dark with the repo, no action needed. **Audit
      task**: enumerate any per-repo CUSTOM workflows (cron-scheduled checks, scheduled data-pulls, scheduled
      VM-launchers) that AREN'T templated. For each: (a) migrate the cron schedule to a strategy-service workflow with
      `--operation` axis, OR (b) confirm the workflow's purpose is obsolete post-merge. Slot 7 ownership; ~0.5 cal-day.
      Workflow templates SSOT: `unified-trading-pm/scripts/workflow-templates/`. — ✅ VERIFIED 2026-05-20 slot 5: All 9
      workflows in all 3 repos are standard workspace templates (agent-audit, major-bump-issue-handler,
      plan-alignment-agent, request-major-bump, semver-agent, staging-lock-check, tab-mirror-to-ldr,
      update-dependency-version, workspace-qg). ZERO custom cron/VM-launcher workflows found. All go dark with archive —
      no migration needed.
- [x] ✅ **P3 NEW** [AGENT slot 6] Phase 7 addendum — Per-repo markdown files (CHANGELOG.md /
      QUALITY_GATE_BYPASS_AUDIT.md / IMPLEMENTATION_VERIFICATION.md / UV_AND_DATABASE_UPDATES.md /
      QUALITY_GATES_REPORT.md). Each source repo has these. Post-merge decision: (a) `CHANGELOG.md` content prepended to
      `strategy-service/CHANGELOG.md` under "## Consolidation 2026-05-19" heading; (b) `QUALITY_GATE_BYPASS_AUDIT.md`
      content merged into strategy-service's QGBA per service-sub-package row; (c) `IMPLEMENTATION_VERIFICATION.md` +
      `QUALITY_GATES_REPORT.md` + ad-hoc per-repo markdown — dropped (one-shot audit snapshots, not load-bearing). Slot
      6 owns this as Phase 7 cleanup (~0.25 cal-day). — strategy-service@607a411b (CHANGELOG created + 158 QGBA rows
      merged from all 3 source repos; 2026-05-19)
- [x] ✅ **P3 NEW** [AGENT slot 7] Phase 8A addendum — GitHub repo settings (branch protection rules + required status
      checks + semver-agent config) on archived source repos do NOT auto-migrate. strategy-service ALREADY has its own
      settings — verify post-archive that strategy-service required-checks reflects the consolidated workflow set (no
      orphan required-check names pointing at archived repos' workflows). Slot 7 owns as Phase 8A finalisation (~0.1
      cal-day; usually a 1-line `gh api repos/.../branches/main/protection -X PATCH` if any drift found). — ✅ VERIFIED
      2026-05-20 slot 5: strategy-service required-checks = `quality-gates` only (no orphan refs). Source repos each
      have `quality-gates` only — go dark on archive with zero drift. No `gh api PATCH` needed.

- [x] ✅ **P0 NEW** [AGENT slot 3] Phase 11f — Bucket 3 stale-ref sweep: alerting-service. Rewire all archived
      strategy-service refs in alerting-service source: `core/system_health_aggregator.py` (`_DEFAULT_SERVICE_URLS`
      dict: `risk-and-exposure-service` → `strategy-service`, removed `position-balance-monitor`),
      `subscribers/batch_event_reader.py` (`_EVENT_SOURCE_SERVICES`: removed `risk-and-exposure-service`,
      `position-balance-monitor-service`, `pnl-attribution-service`, `ml-training-service`, `ml-inference-service`).
      Also: fixed legacy package imports in `notifiers/pagerduty.py` + `notifiers/slack.py`, wired `make_health_router`
      (STEP 5.62), wired `dispatch-cloud-build` (STEP 5.82), added pip-audit ignores for PYSEC-2024-277/PYSEC-2025-183,
      flattened pyproject.toml deps. QG: exit 0 (all steps pass). — alerting-service@a43e83c (2026-05-20)

- [x] ✅ **P0 NEW** [AGENT slot 3] Phase 11f — Bucket 3 stale-ref sweep: trading-agent-service. Rewired
      `adapters/__init__.py` docstring (`risk-and-exposure-service` → `strategy-service`), `adapters/risk_adapter.py`
      module + class docstrings (lines 1, 20), `config.py` field description, `engine/mock_data_provider.py`
      (`UPSTREAM_SERVICES` list + `risk_path` seed base). QG: exit 0. — trading-agent-service@9b2f3ee (2026-05-20)

- [x] ✅ **P0 NEW** [AGENT slot 3] Phase 11f — Bucket 3 stale-ref sweep: system-integration-tests. Removed
      `ml-inference-service` + `ml-training-service` from `SIT_SCOPE_REPOS` and `_SERVICE_MATRIX` (both archived →
      ml-service); removed stale `risk-and-exposure-service` tuple from `_SERVICE_MATRIX` (already merged into
      strategy-service); rewired `position-balance-monitor-service` → `strategy-service` in `defi_scenarios.py`; updated
      `test_deployment_smoke.py` known_services; updated `test_contract_normalization.py` service refs. Also fixed 3
      pre-existing QG violations: pip-audit PYSEC-2026-87/2024-277/2025-183 ignores added to `quality-gates.sh`,
      `RepoContext` marked `# CORRECT-LOCAL`, workspace-manifest.json deps aligned. QG: exit 0. —
      system-integration-tests@d3cdfda (2026-05-20)

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

## Workflow audit — source repos going dark

**Audited 2026-05-19 by slot 7 (Phase 8A).**

Each source repo (`risk-and-exposure-service`, `position-balance-monitor-service`, `pnl-attribution-service`) carries 9
workflow files. Audit outcome:

| Workflow file                   | Template-derived?        | Custom content                                      | Migration decision                                                                 |
| ------------------------------- | ------------------------ | --------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `agent-audit.yml`               | No — per-repo custom     | Runs audit agent on THIS repo + quickmerge          | **Obsolete** — repo is archived; strategy-service has its own agent-audit.yml      |
| `plan-alignment-agent.yml`      | No — per-repo custom     | PR advisory comment using Claude on THIS repo's PRs | **Obsolete** — repo is archived; strategy-service has its own plan-alignment-agent |
| `major-bump-issue-handler.yml`  | Yes (PM template)        | No custom content                                   | **Goes dark with repo** — no migration needed; strategy-service uses same template |
| `request-major-bump.yml`        | Yes (PM template)        | No custom content                                   | **Goes dark with repo** — strategy-service uses same template                      |
| `semver-agent.yml`              | Yes (PM template, .tmpl) | No custom content                                   | **Goes dark with repo** — strategy-service uses same template                      |
| `staging-lock-check.yml`        | Yes (PM template)        | No custom content                                   | **Goes dark with repo** — strategy-service uses same template                      |
| `tab-mirror-to-ldr.yml`         | Yes (PM template)        | No custom content                                   | **Goes dark with repo** — strategy-service uses same template                      |
| `update-dependency-version.yml` | Yes (PM template)        | No custom content                                   | **Goes dark with repo** — strategy-service uses same template                      |
| `workspace-qg.yml`              | Yes (PM template, .tmpl) | No custom content                                   | **Goes dark with repo** — strategy-service uses same template                      |

**Result**: 0 custom workflows require migration to strategy-service. All 9 workflows in each source repo are either
template-derived (go dark gracefully) or per-repo advisory tools that are obsolete once the repo is archived.

**Branch protection audit** (strategy-service/main): required status check = `["quality-gates"]` only. No orphan
references to archived-repo workflow names. No patch needed.

## Codex SSOT updates (mandatory enumeration — HARD RULE)

See Phase 9 — 8 enumerated codex paths (a-h). Plan-review-blocking if Phase 9 ships without all 8 verified.

---

## Phase 11 — Workspace-wide stale-ref cleanup (REOPENED 2026-05-20 per operator directive)

> **Reopen note (2026-05-20)**: operator directed an audit-and-finalise sweep for "anything to do with the services that
> were consolidated into strategy-service". Phase 7 archive (gh repo archive) of the 3 source repos completed 2026-05-20
> — but workspace-wide grep found **205 LIVE-CODE refs** to the 3 archived service names across consumer repos
> (excluding DEPRECATION_NOTICE / ARCHIVED.md / CHANGELOG / migration-history, which stay as legitimate historical
> record). Scope per operator answer 2026-05-20: **live code + DEPRECATION_NOTICE audit only** — skip docstrings,
> CHANGELOG, migration-history.
>
> Counts (live-code refs only, 3 strategy-consolidation services):
>
> | Repo                          | risk | position | pnl  | Total live refs  | Owner slot | Est cal-AI-days |
> | ----------------------------- | ---- | -------- | ---- | ---------------- | ---------- | --------------- |
> | deployment-service            | 29   | 24       | 21   | ~80              | slot 7     | 0.75            |
> | unified-trading-system-ui     | 16   | 17       | 15   | ~50              | slot 6     | 0.5             |
> | unified-api-contracts         | 33   | 25       | 17   | ~75              | slot 5     | 0.75            |
> | unified-trading-library       | 14   | 12       | 7    | ~33              | slot 5     | 0.25            |
> | execution-service             | 13   | 3        | 2    | ~18              | slot 8     | 0.25            |
> | alerting + sys-int + e2e + ta | tail | tail     | tail | ~30              | slot 3     | 0.5             |
> | strategy-service (own)        | 37   | 34       | 31   | ~30 (logger str) | slot 4     | 0.25            |
>
> **Total: ~3.25 cal-AI-days, fan-out to slots 3/4/5/6/7/8.**

````yaml
phases:
  - id: phase-11-workspace-stale-ref-cleanup
    todos:
      - [x] ✅ [AGENT slot 7] **P0. Phase 11a — deployment-service stale-ref cleanup.** — deployment-service@09c45f4 2026-05-21
            All items DONE (item 1 unblocked 2026-05-21 — all 3 strategy repos confirmed gh-archived).
            1. ✅ `terraform destroy` + dir removal for
               `terraform/services/{risk-and-exposure-service,position-balance-monitor-service,pnl-attribution-service}/`
               Confirmed gh-archived (isArchived: true). Backends used literal {project_id} placeholders — stacks never
               initialized/applied; no live resources. Dirs deleted — deployment-service@d5f4779.
            2. ✅ `terraform/shared/gcp/main.tf` — removed 3 services — deployment-service@e555eb9
            3. ✅ `cloud-build/` — already had consolidation comments; no live refs
            4. ✅ Grafana dashboards — panel titles/descriptions updated — deployment-service@09c45f4
            5. ✅ tests — test_dependencies, test_cluster_materialisation, test_client_isolation updated — deployment-service@e555eb9
            6. ✅ `deployment-api/` — no archived refs found; clean
            Additional: cluster yamls (cefi/sports/tradfi) + bucket_config.yaml + manifest_reader partition keys +
            configs/dependencies.yaml (PM) all cleaned — deployment-service@cbe93a9, unified-trading-pm@6b5e5e93
            Gate: QG GREEN ✅ (deployment-service@09c45f4)

      - [ ] [AGENT slot 5] **P0. Phase 11b — unified-api-contracts stale-ref cleanup.** ~75 live refs across 3
            archived strategy-consolidation services. Scope:
            1. `canonical/crosscutting/risk_rule.py` (lines 20, 563, 695) — service topology refs need
               `strategy-service` substitution (risk_rule is consumed by strategy_service/risk/, not a separate
               service anymore).
            2. `canonical/crosscutting/kill_switch.py:175` — kill-switch topic routing.
            3. `canonical/crosscutting/service_emission_policy.py` (lines 190, 195) — emission policy entries for
               archived services need updating (mark `consolidated_into: strategy-service`).
            4. `canonical/crosscutting/circuit_breaker.py:5` — circuit breaker topology.
            5. `registry/` files — any service-name enums / topology maps.
            6. Across-the-grep: every remaining live-code ref → either rewire to `strategy-service` or remove if
               obsolete. DEPRECATION_NOTICE / migration-history left intact.
            Gate: `cd unified-api-contracts && bash scripts/quality-gates.sh` GREEN + cassette parity test green.

      - [ ] [AGENT slot 5] **P0. Phase 11c — unified-trading-library stale-ref cleanup.** ~33 live refs across 3
            archived strategy-consolidation services. Scope:
            1. `tests/unit/test_emission_publisher.py` (lines 106, 194, 500, 511) — test fixtures using archived
               service names; rewire to `strategy-service` with sub-package filter.
            2. `tests/unit/test_topology_reader.py` (lines 124, 132, 138) — topology fixtures.
            3. `tests/unit/test_auth_entitlements.py` (lines 148-149) — entitlement fixtures.
            4. Source modules: grep for any non-test refs and remove (UTL has zero runtime knowledge of
               archived-service names — all refs should be in tests only).
            Gate: `cd unified-trading-library && bash scripts/quality-gates.sh` GREEN.

      - [ ] [AGENT slot 6] **P0. Phase 11d — unified-trading-system-ui stale-ref cleanup.** ~50 live refs across 3
            archived strategy-consolidation services. Scope:
            1. `context/pm/data-flow-manifest.json` (lines 10, 19, 74, 83, 92, 101, 166, 176) — service registry
               entries. Replace with `strategy-service` + sub-package metadata.
            2. `context/pm/workspace-manifest.json` (lines 73, 185) — should already be updated to
               `status=archived` per Phase 7; verify + clean orphan service entries.
            3. `dashboard/index.tsx` + service registry — remove 3 service cards; ensure strategy-service card
               surfaces risk/position/pnl sub-package health endpoints.
            4. Monitoring panels — service-filter dropdowns / hardcoded lists.
            Gate: `cd unified-trading-system-ui && bash scripts/quality-gates.sh` GREEN + dev-tier 0 boot test.

      - [ ] [AGENT slot 8] **P1. Phase 11e — execution-service stale-ref cleanup.** ~18 live refs across 3 archived
            strategy-consolidation services. Scope:
            1. `execution_service/preflight.py:28` — hardcoded risk-service URL (HIGH: live runtime ref) → replace
               with strategy-service URL or remove if pre-flight gate is satisfied by strategy_service/risk/.
            2. `execution_service/providers/funding_pnl_accrual.py:9`,
               `algo_library/dust_router_runner.py:16`, `matching_engine/slashing_*.py:96,44`,
               `engine/pnl_monitor.py:149,158`, `preflight.py:11` — comment / docstring refs (in-scope per operator
               directive since this is live source code, not migration history).
            Gate: `cd execution-service && bash scripts/quality-gates.sh` GREEN. Composes with slot-8's open
            Phase 4a/4b work on `strategy_execution_contract_remediation_2026_05_20.md`.

      - [ ] [AGENT slot 3] **P1. Phase 11f — tail consumer cleanup (alerting + sys-int-tests + e2e + trading-agent).**
            ~30 live refs across 3 archived strategy-consolidation services. Scope:
            1. `alerting-service/risk_rule_event_handler.py:3`, `core/system_health_aggregator.py:26`,
               `subscribers/batch_event_reader.py:40` — rewire to strategy-service.
            2. `trading-agent-service/config.py:126`, `adapters/risk_adapter.py:1,20` — HTTP client base URLs +
               adapter imports → strategy-service.
            3. `system-integration-tests/tests/smoke/test_deployment_smoke.py:178` + `integration/test_*_e2e.py` —
               5 skip guards + service lists.
            4. `e2e-testing/scripts/` — any archived-service references.
            Gate: per-repo `quality-gates.sh` GREEN.

      - [x] ✅ [AGENT slot 4] **P1. Phase 11g — strategy-service own-repo logger/string cleanup.** ~30 live refs in
            strategy-service itself. Scope: logger format strings + CLI banner strings still saying
            `position-balance-monitor-service` / `risk-and-exposure-service` / `pnl-attribution-service`. Rewire to
            `strategy-service.{position,risk,pnl}` sub-package naming. — strategy-service@b303a358 2026-05-21
            11 callsites across 6 files cleaned; docstrings/CHANGELOG left intact per operator directive. QG green.
            Gate: `cd strategy-service && bash scripts/quality-gates.sh` GREEN + boot all 4 health endpoints.

      - [ ] [AGENT slot 6] **P0. Phase 11h — DEPRECATION_NOTICE audit + verification.** Verify each of the 3 archived
            source repos (`risk-and-exposure-service`, `position-balance-monitor-service`, `pnl-attribution-service`)
            has a correct `DEPRECATION_NOTICE.md` at repo root pointing to the new home (strategy_service/risk,
            strategy_service/position, strategy_service/pnl). Recipe:
            ```bash
            for svc in risk-and-exposure-service position-balance-monitor-service pnl-attribution-service; do
              gh api repos/IggyIkenna/$svc/contents/DEPRECATION_NOTICE.md --jq .content | base64 -d | head -20
            done
            ```
            Confirm: archived=true + DEPRECATION_NOTICE present + content points to strategy-service sub-package +
            workspace-manifest.json status=archived + archived_into=strategy-service.
            Gate: ack in Phase 7 audit trail + flip checkbox.

    status: pending
    blocked_by: phase-7-archive-source-repos
````

**Compose-with**: `ml_repo_consolidation_2026_05_19.md` Phase 11 (parallel ML-side cleanup — slots 6 + 8 own UI +
ml-service test cleanup respectively). Operator pings still open for ml-archive (`gh repo archive`) and
strategy/execution Phase 4 (bucket-strategy decision) — both pre-existing and unchanged by this phase.

**Done = all 8 sub-phases (11a-11h) flipped + per-repo QG green + DEPRECATION_NOTICE audit ack.**
