---
name: cicd-code-rollout-master-2026-03-13
overview: >
  Master rollout plan consolidating 16 active plans into a single milestone-gated execution sequence. Covers: CI/CD
  pipeline bug fixes (7 bugs), citadel-grade hardening (SIT debounce, starvation detection, Telegram rate-limiting,
  manifest atomicity), workflow rollout to all 65 repos (composite actions, semver-agent, conflict-resolution-agent),
  library tier completion (T0->T1->T2->T3 with invariant enforcement), service/UI hardening (19 services, 10 APIs, 13
  UIs), deployment infrastructure (AWS, IBKR, DeFi testnet, dev onboarding), features (cloud mode indicator, Grafana,
  Elysium fork, user management), and the 1.0.0 stability gate with full production readiness audit. Each phase has exit
  criteria; next phase starts only when current passes.
type: mixed
epic: epic-infra
status: active

completion_gates:
  code: C5
  deployment: D5
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C5
    deployment: none
    business: none
    readiness_note: "Orchestrator repo. All 23 workflows hardened, diagram SSOT current."
  - repo: system-integration-tests
    code: C4
    deployment: none
    business: none
    readiness_note: "SIT passes on main with full service stack."

depends_on: []
  # This is the master plan. Other plans depend on it, not the reverse.
  # Inter-plan blocker: Plan 3 (DeFi Keys) Phase 1 blocks this plan's Phase 5 (backfill needs API keys).

supersedes:
  - master_pre_deployment_plan_chain
  - code_readiness_master_plan_2026_03_11
  - phase2_library_tier_hardening
  - phase3_service_hardening_integration
  - cicd_audit_remediation_2026_03_13
  - full_autonomous_agent_ci
  - conflict_resolution_agent_2026_03_13
  - composite_action_qg_inheritance_2026_03_12
  - aws_migration
  - dev_environment_automated_onboarding_2026_03_10
  - ibkr_gateway_rollout
  - user_management_platform_2026_03_13
  - ui_cloud_mode_indicator_2026_03_12
  - strategy_visibility_grafana_2026_03_10
  - elysium_defi_system_fork_2026_03_10

todos:
  # ── Phase 0: CLEANUP ──────────────────────────────────────────────────────
  # Exit criteria: Zero stale artifacts, all known bugs catalogued

  - id: cleanup-delete-stale-develop-branch
    content: >
      [SCRIPT] P0. Delete stale execution-service `develop` branch. Only repo with it — confirmed stale, all repos use
      three-tier model (feat/*/staging/main). Command: `cd execution-service && git push origin --delete develop`.
      Verify: `git ls-remote --heads origin develop` returns empty.
    status: done

  - id: cleanup-fix-telegram-if-guard
    content: >
      [AGENT] P0. Fix BUG-1: Telegram `if:` guard broken in 3 PM workflows. `env.TELEGRAM_BOT_TOKEN` is unavailable in
      GHA `if:` expressions (only in step-level env). Files: `semver-agent.yml:435`, `rules-alignment-agent.yml:197`,
      `plan-health-agent.yml:89`. Fix: replace `if: always() && env.TELEGRAM_BOT_TOKEN != ''` with `if: always()` and
      add early-exit inside run block: `if [ -z "$TELEGRAM_BOT_TOKEN" ]; then echo "No token, skipping"; exit 0; fi`.
      Ensure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are in the step's `env:` block (where secrets ARE accessible).
    status: done

  - id: cleanup-fix-telegram-chat-id-secret
    content: >
      [AGENT] P0. Fix BUG-2: `conflict-resolution-merged.yml:68` uses `secrets.TELEGRAM_CHAT_ID` but should use
      `vars.TELEGRAM_CHAT_ID` (repository variable, not secret). Fix the reference.
    status: done

  - id: cleanup-verify-semver-agent-trigger
    content: >
      [SCRIPT] P1. Verify semver-agent trigger = `branches: [staging]` (not main) across all 65 deployed copies. Script:
      for each repo in manifest, check `.github/workflows/semver-agent.yml` line with `branches:`. Report any repo with
      wrong trigger. Template at `scripts/propagation/templates/semver-agent.yml` already has `branches: [staging]` —
      verify deployed copies match.
    status: done

  - id: cleanup-add-orchestrator-concurrency
    content: >
      [AGENT] P1. Fix BUG-6: overnight-agent-orchestrator has no concurrency guard. If cron fires while previous run
      still active, two instances overlap. Add `concurrency: { group: overnight-orchestrator, cancel-in-progress: true
      }` to `overnight-agent-orchestrator.yml`. The newer run should take precedence.
    status: done

  - id: cleanup-fix-cloud-build-timeout
    content: >
      [AGENT] P1. Fix BUG-5: Cloud Build polling in `cloud-build-router.yml` doesn't cleanly distinguish build TIMEOUT
      (Cloud Build reports TIMEOUT status) from poll TIMEOUT (our loop exceeds MAX_POLLS). Fix: add explicit exit codes
      — 0 on SUCCESS, 1 on build FAILURE/TIMEOUT/CANCELLED, 2 on poll exhaustion. Each gets a distinct Telegram message.
    status: done

  - id: cleanup-fix-version-mismatch
    content: >
      [SCRIPT] P1. Fix BUG-7: instruments-service manifest version `0.1.22` vs pyproject.toml `0.1.117`. Scan ALL repos
      for same drift pattern. Script: for each repo, compare `versions[repo]` in manifest with version in
      `pyproject.toml`. Report all mismatches. Fix by updating manifest to match pyproject (pyproject is source of truth
      for current version).
    status: done

  - id: cleanup-update-index
    content: >
      [AGENT] P2. Update `plans/active/INDEX.md` — register 5 new master plans, mark all 26 old plans as superseded with
      `superseded_by:` references.
    status: done

  # ── Phase 1: CI/CD HARDENING ──────────────────────────────────────────────
  # Exit criteria: All 7 bugs fixed, all citadel enhancements deployed, zero silent failure paths
  # Blocker: Phase 0 complete

  - id: harden-fix-sha-pinning-toctou
    content: >
      [AGENT] P0. Fix BUG-3: SHA pinning TOCTOU in `staging-to-main.yml`. Between SIT completing and the merge PR being
      created, a concurrent push could land on staging that bypasses SIT validation. Fix: after checkout of each repo's
      staging branch, verify `git rev-parse HEAD` matches the SHA recorded in `staging_commits[repo]`. If mismatch and
      the new commits are NOT `[skip ci]`-only, abort the promotion and re-trigger SIT. Current code allows `[skip ci]`
      descendants — preserve that.
    status: done
    depends_on: [cleanup-fix-telegram-if-guard]

  - id: harden-validate-conflict-agent-output
    content: >
      [AGENT] P0. Fix BUG-4: conflict-resolution-agent doesn't validate Claude output. Add validation after parsing `===
      filename ===` markers: (a) every file in the conflict list must appear in output, (b) no `<<<<<<<` / `=======` /
      `>>>>>>>` markers remain in resolved files, (c) Python files pass `py_compile`, YAML files pass
      `yaml.safe_load()`. If validation fails, skip push and send Telegram "resolution incomplete — manual intervention
      required" with the failing file list.
    status: done
    depends_on: [cleanup-fix-telegram-if-guard]

  - id: harden-audit-manifest-concurrency
    content: >
      [AGENT] P0. Audit all 5 manifest-mutating workflows share `concurrency: { group: manifest-update,
      cancel-in-progress: false }`. Workflows: `update-repo-version.yml`, `staging-to-main.yml`, `sit-gate.yml`,
      `sit-unlock.yml`, `hotfix-mode.yml`. Add to any that are missing.
    status: done

  - id: harden-wire-cloud-build-telegram
    content: >
      [AGENT] P1. Wire Cloud Build failure alerts to Telegram in `cloud-build-router.yml`. Include: repo name, commit
      SHA, build log URL, failure reason, and environment (dev/staging/prod). Currently only SUCCESS path updates
      manifest — add FAILURE path with Telegram alert.
    status: done

  - id: harden-create-composite-qg-action
    content: >
      [AGENT] P1. Create `run-quality-gates` composite action in `.github/actions/run-quality-gates/action.yml`. This
      centralizes QG boilerplate so per-repo workflows become ~20 lines. Inputs: SERVICE_NAME, SOURCE_DIR, MIN_COVERAGE,
      python-version (default 3.13.9), basedpyright-version (default 1.38.2). Existing actions `setup-python-tools` and
      `setup-ui-tools` already exist — build on them. Test with instruments-service as canary.
    status: done

  - id: harden-add-sit-debounce
    content: >
      [AGENT] P1. Add SIT debounce — if multiple repos merge to staging in rapid succession, SIT should wait for a
      5-minute quiet period (no new staging merges) before triggering. Implementation: `sit-gate.yml` records
      `staging_status.pending_repos[]` list with timestamps. A scheduled workflow (every 5 min) checks if the list has
      been stable for 5 minutes — if so, triggers SIT. This prevents redundant SIT runs and wasted compute.
    status: done

  - id: harden-cascade-starvation-detector
    content: >
      [AGENT] P2. Add cascade starvation detection — if `staging_status.locked=true` persists for >1 hour, send Telegram
      alert "SIT lock stale — staging has been locked for >1hr. Check SIT status or force-unlock." Implementation:
      scheduled workflow (every 15 min) reads `staging_status.locked` and `staging_status.locked_at` timestamp. If
      locked and age >1hr, alert once (dedup via `locked_alert_sent` flag).
    status: done

  - id: harden-telegram-rate-limit
    content: >
      [AGENT] P2. Add Telegram rate-limit guard — max 1 alert per workflow per 60 seconds. Prevents rapid cascades from
      spamming the channel. Implementation: add `handle-claude-api-error`-style composite action for Telegram that
      checks last-alert timestamp in workflow artifacts or manifest.
    status: done

  - id: harden-integrate-diagram-regen
    content: >
      [AGENT] P2. Integrate CI/CD diagram auto-regen into PM quality-gates.sh post-gates step. Currently exists as
      standalone `scripts/generate-cicd-diagram.py`. Add to QG so every PM quickmerge that touches
      `cicd-pipeline-definition.yaml` auto-regenerates SVG/HTML. (May already be done per cicd_audit plan — verify and
      close if so.)
    status: done

  - id: harden-audit-manifest-atomicity
    content: >
      [SCRIPT] P2. Audit all manifest writes for atomic tmp+rename pattern. All 5 manifest-mutating workflows should
      write to `.json.tmp` then `os.replace()` (or `mv`) to prevent corruption on concurrent access. Scan and report any
      that write directly to `workspace-manifest.json`.
    status: done

  # ── Phase 2: WORKFLOW ROLLOUT TO ALL REPOS ─────────────────────────────────
  # Exit criteria: All 65 repos have consistent CI using composite actions; ci_status promoted
  # Blocker: Phase 1 complete

  - id: rollout-composite-qg-workflows
    content: >
      [SCRIPT] P0. Roll out thin QG workflows using composite actions to all 65 repos. Script reads
      `workspace-manifest.json` for dep lists per repo, generates slim `quality-gates.yml` (~20 lines) that calls the
      composite action. Verify by triggering QG on 3 canary repos (one per tier).
    status: pending
    depends_on: [harden-create-composite-qg-action]

  - id: rollout-corrected-semver-agent
    content: >
      [SCRIPT] P0. Roll out corrected `semver-agent.yml` to all repos using
      `scripts/propagation/rollout-agent-workflows.sh`. Simultaneously REMOVE old `version-bump.yml` from each repo
      (semver-agent replaces it). Verify all 65 have `branches: [staging]`.
    status: pending
    depends_on: [cleanup-verify-semver-agent-trigger]

  - id: rollout-conflict-resolution-agent
    content: >
      [AGENT] P1. Deploy conflict-resolution-agent.yml to PM (already exists as of audit). Wire dispatch: (a)
      `staging-to-main.yml` dispatches `merge-conflict-detected` when `mergeable_state=dirty`, (b)
      `feature-branch-to-staging.yml` template dispatches on merge conflicts. Include BUG-4 output validation from Phase
      1. Test with deliberate conflict on instruments-service.
    status: done
    depends_on: [harden-validate-conflict-agent-output]

  - id: rollout-artifact-registry
    content: >
      [AGENT] P1. Set up GCP Artifact Registry for Python packages. Currently all repos use editable local installs via
      `[tool.uv.sources]` with `path = "../<repo>"`. This works locally but breaks in CI where sibling repos aren't
      checked out. Create AR repository, publish T0 libraries as wheels, update CI workflows to install from AR when
      local path unavailable.
    status: pending

  - id: rollout-promote-ci-status
    content: >
      [SCRIPT] P1. Run QG on all repos; promote `ci_status` from `BASELINE_RECORDED` to `VALIDATED` where passing.
      Currently 46/65 repos stuck at BASELINE_RECORDED. Script: for each repo, run `bash scripts/quality-gates.sh`, if
      exit 0 then update manifest `ci_status` to `VALIDATED`.
    status: pending

  - id: rollout-dependency-update-template
    content: >
      [SCRIPT] P2. Roll out `update-dependency-version.yml` template to all repos. This workflow receives
      `dependency-update` dispatch from PM and updates pyproject.toml constraints with `[skip ci]` commit.
    status: pending

  # ── Phase 3: LIBRARY TIER COMPLETION (T0->T1->T2->T3) ─────────────────────
  # Exit criteria: All library tiers at CR5, coverage >= 70%, basedpyright clean
  # Blocker: Phase 2 complete; T0->T1->T2->T3 invariant enforced

  - id: library-t0-d4d5
    content: >
      [AGENT per repo] P0. T0 (6 repos): D4/D5 — QG pass + quickmerge to main. D1-D3 already PASS. Repos:
      unified-api-contracts, unified-internal-contracts, unified-events-interface, unified-cloud-interface,
      execution-algo-library, matching-engine-library. For each: run `bash scripts/quality-gates.sh` (Pass 1), then
      quickmerge (Pass 2). All 6 must reach CR5 before T1 starts.
    status: pending
    depends_on: [rollout-composite-qg-workflows]

  - id: library-t1-harden
    content: >
      [AGENT per repo] P0. T1 (3 repos): coverage 70%, basedpyright strict, integration tests for dep edges (UTL->UEI,
      URDI->UCI, UCI->UEI), quickmerge. Repos: unified-trading-library, unified-reference-data-interface,
      unified-config-interface. T0 invariant: all T0 repos must be at CR5 before starting T1.
    status: pending
    depends_on: [library-t0-d4d5]

  - id: library-t2-harden
    content: >
      [AGENT per repo] P1. T2 (7 repos): fix basedpyright errors (UMI 67, UDEI 78), coverage 70%, quickmerge. Repos:
      unified-market-interface, unified-trade-execution-interface, unified-ml-interface,
      unified-feature-calculator-library, unified-defi-execution-interface, unified-position-interface,
      unified-sports-execution-interface. T1 invariant: all T1 repos must be at CR5 before starting T2.
    status: pending
    depends_on: [library-t1-harden]

  - id: library-t3-harden
    content: >
      [AGENT] P1. T3 (1 repo): coverage 70%, basedpyright, quickmerge. Repo: unified-domain-client. T2 invariant: all T2
      repos must be at CR5 before starting T3.
    status: pending
    depends_on: [library-t2-harden]

  - id: library-publish-ar
    content: >
      [SCRIPT] P1. Publish all T0-T3 libraries to GCP Artifact Registry as versioned wheels. Each library gets a wheel
      published on every main merge via `publish-package.yml` workflow update.
    status: pending
    depends_on: [rollout-artifact-registry, library-t0-d4d5]

  # ── Phase 4: SERVICE & UI HARDENING ────────────────────────────────────────
  # Exit criteria: All services/APIs/UIs at CR4+, vitest in all UI repos, SIT passes
  # Blocker: Phase 3 complete

  - id: service-l7l8-harden
    content: >
      [AGENT per repo] P0. L7-L8 (19 T4 services): coverage 70%, basedpyright, integration tests, quickmerge. Expand
      execution-service QG script beyond 59 lines (audit §2 FAIL). Repos: instruments-service (L7), alerting-service,
      execution-service, features-calendar-service, features-cross-instrument-service, features-delta-one-service,
      features-multi-timeframe-service, features-onchain-service, features-sports-service, features-volatility-service,
      features-commodity-service, market-data-processing-service, market-tick-data-service, ml-inference-service,
      ml-training-service, pnl-attribution-service, strategy-service, trading-agent-service, elysium-defi-system (L8).
    status: pending
    depends_on: [library-t3-harden]

  - id: service-l9-harden
    content: >
      [AGENT per repo] P1. L9 (10 T5 API+operational): coverage, basedpyright, quickmerge. Repos: batch-audit-api,
      client-reporting-api, execution-results-api, market-data-api, ml-inference-api, ml-training-api,
      position-balance-monitor-service, risk-and-exposure-service, strategy-validation-service, trading-analytics-api.
    status: pending
    depends_on: [service-l7l8-harden]

  - id: service-l10-harden
    content: >
      [AGENT per repo] P1. L10 (4 deployment infra): deployment-api, deployment-service,
      batch-live-reconciliation-service, unified-trading-ui-kit.
    status: pending
    depends_on: [service-l9-harden]

  - id: service-l11-ui-harden
    content: >
      [AGENT per repo] P1. L11 (13 UIs): TypeScript strict, vitest (add to 3 missing: trading-analytics-ui,
      execution-analytics-ui, batch-audit-ui — audit §16 FAIL), Playwright smoke tests where applicable. All 13 UI
      repos.
    status: pending
    depends_on: [service-l10-harden]

  - id: service-full-sit
    content: >
      [SCRIPT] P0. Full SIT validation with all services on staging. Run system-integration-tests against the full
      service stack. All tests must pass.
    status: pending
    depends_on: [service-l11-ui-harden]

  # ── Phase 5: DEPLOYMENT INFRASTRUCTURE ─────────────────────────────────────
  # Exit criteria: AWS canary validated, IBKR gateway live, DeFi testnet provisioned, dev onboarding automated
  # Blocker: Phase 3 complete; AWS account creation [HUMAN]

  - id: deploy-aws-account
    content: >
      [HUMAN] P1. AWS account creation + IAM roles + Terraform validate. This is the gating blocker for all AWS work.
      From aws_migration plan: Phase 0a-0f (account setup, team access, GitHub credentials, region selection, service
      roles, quota review).
    status: pending

  - id: deploy-aws-codebuild-canary
    content: >
      [SCRIPT] P2. AWS CodeBuild canary — validate `buildspec.aws.yaml` (distributed to all 66 repos) actually works.
      Run simulated CodeBuild for 3 canary repos: instruments-service, UCI, UEI.
    status: pending
    depends_on: [deploy-aws-account]

  - id: deploy-ibkr-gateway
    content: >
      [HUMAN+AGENT] P2. IBKR gateway: add credentials to Secret Manager (VM already running at 34.146.71.13),
      consolidate 4 duplicated IBKR adapters into thin shims pointing to ibkr-gateway-infra. Repos: ibkr-gateway-infra,
      UMI, UTEI, UPI, URDI, UCI.
    status: pending

  - id: deploy-defi-testnet
    content: >
      [AGENT] P2. DeFi dev testnet: create DeFi venue matrix SSOT document, Terraform dev environment provisioning for
      Sepolia/Tenderly/Hyperliquid testnet, retire old setup scripts.
    status: pending

  - id: deploy-dev-onboarding
    content: >
      [AGENT] P3. Automated developer onboarding script — `setup-dev-environment.sh` that takes a developer from clean
      macOS to fully working local environment in <15 minutes. Covers gcloud, aws CLI, docker, .env files, workspace
      bootstrap.
    status: pending

  # ── Phase 6: FEATURES & STABILITY GATE ─────────────────────────────────────
  # Exit criteria: All features deployed, T0 repos at 1.0.0+, audit grade A (0 FAILs)
  # Blocker: Phases 4-5 complete

  - id: feature-cloud-mode-indicator
    content: >
      [AGENT] P2. Cloud mode indicator in all UIs. Add `/api/health` response with `cloud_provider` + `mock_mode` to all
      API repos. Add dynamic badge component to all 12 UI repos.
    status: pending

  - id: feature-grafana
    content: >
      [AGENT+HUMAN] P2. Grafana deployment on Cloud Run + 5 dashboards (strategy, execution, PnL, signals, risk). Add
      Prometheus metrics to strategy/execution/PnL services. Embed panels in unified-admin-ui.
    status: pending

  - id: feature-elysium-fork
    content: >
      [AGENT] P2. Elysium DeFi system fork — standalone repo with DeFi strategy/execution components. Replace 8 stub
      handlers with implementations. Docker build produces working image.
    status: pending

  - id: feature-user-management
    content: >
      [AGENT] P2. User management platform — role-based access, authentication, admin portal.
    status: pending

  - id: stability-1-0-0-promotion
    content: >
      [SCRIPT+HUMAN] P0. 1.0.0 promotion for all repos. Order: T0 first via `feat!:` commit (triggers MINOR bump on
      0.x.x per pre-1.0.0 rule — so this needs a manual version set or policy override to cross to 1.0.0). Then
      T1->T2->T3 respecting tier invariant. Verify version cascade propagates cleanly at each tier. Human approves each
      tier promotion.
    status: pending
    depends_on: [service-full-sit]

  - id: stability-production-audit
    content: >
      [AGENT] P0. Full 28-section production readiness audit using
      `unified-trading-codex/10-audit/trading_system_audit_prompt.md`. Target: grade A (0 FAILs, max 3 WARNs). Must
      resolve all 6 FAILs from 2026-03-11 audit: §2 execution-service QG expanded, §5 float isolation verified, §7 T0 at
      1.0.0, §9 all plans registered + ci_status promoted, §10 VCR cassettes in 3 interfaces, §16 vitest in 3 UIs.
    status: pending
    depends_on: [stability-1-0-0-promotion]

  - id: stability-final-sit
    content: >
      [SCRIPT] P0. Final SIT validation on main — all-green gate before live trading. Run system-integration-tests
      against all services on main branch.
    status: pending
    depends_on: [stability-production-audit]
---

## Notes

### Inter-Plan Blockers

- **Plan 3 (DeFi Keys) Phase 1 blocks this plan's backfill work** — production backfill needs API keys loaded into
  Secret Manager first.
- **This plan's Phase 1 blocks Plan 2 (E2E Testing) Phase 1** — bugs must be fixed before testing validates they're
  fixed.
- **This plan's Phase 3 blocks Plan 3 (DeFi Keys) Phase 2** — VCR cassette recording needs interfaces hardened.
- **This plan's Phase 4 blocks Plan 4 (Presentations)** — demo data needs services deployed.

### Citadel-Grade Design Principles

1. **No silent failures** — every error path produces a Telegram alert or GH issue
2. **No race conditions** — all manifest mutations serialize through `concurrency: manifest-update`
3. **Automated where possible** — [SCRIPT] for deterministic work, [AGENT] for intelligent decisions, [HUMAN] only at
   key decision points
4. **Fast path / slow path** — Phase 0-1 (fixes) can complete in days; Phase 3-4 (hardening) is the slow path respecting
   tier invariants
5. **Milestone-gated** — each phase has exit criteria; no dates, no shortcuts
