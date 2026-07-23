---
doc_type: plan
title: Consolidated Remaining Work
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-02-28"
overview: ""
todos: []
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

---

name: Consolidated Remaining Work overview: | Single source of truth for all remaining todos. Last updated: 2026-02-28.
Supersedes all archived plans.

## Agent Bootstrap — Read This First

Before executing any task in this plan:

1. **Activate workspace venv**:
   `source /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.venv-workspace/bin/activate`
2. **Workspace root**: `WORKSPACE_ROOT=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos`
3. **Quality gates**: ALWAYS use `bash scripts/quickmerge.sh "feat/fix/chore: description"` — NEVER standalone
   `git push` or `bash scripts/quality-gates.sh`
4. **Cursor rules SSOT**: `.cursorrules` + `WORKSPACE_ROOT/.cursor/rules/*.mdc`
5. **Key SSOT docs**:

- Tier architecture: `unified-trading-/codex/04-architecture/TIER-ARCHITECTURE.md`
- Dependency matrix: `unified-trading-/codex/05-infrastructure/unified-libraries/LIBRARY-DEPENDENCY-MATRIX.md`
- Repo registry + versions: `unified-trading-pm/workspace-manifest.json` (all versions are 0.x.x until stable on main)
- GCP auth in tests: `.cursor/rules/gcp-auth-in-tests.mdc`
- Event naming: `unified-trading-/codex/03-observability/lifecycle-events.md`
- CI/CD workflow: `unified-trading-/codex/06-coding-standards/feature-branch-workflow.md`
- Quickmerge (cascade + --no-pr + --unit-only): `.cursor/rules/always-use-quickmerge.mdc`
- Conventional commits: `.cursor/rules/conventional-commits.mdc`
- Integration testing layers (0–3): `unified-trading-/codex/06-coding-standards/integration-testing-layers.md`
- UI → API wiring: `unified-trading-/codex/05-infrastructure/UI-DEPENDENCY-MATRIX.md`
- Runtime topology SSOT (v6): `unified-trading-deployment-v3/configs/runtime-topology.yaml` (sharding dims, event
  triggers, recovery, kill switches, topic templates)
- Topology decisions doc: `unified-trading-/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` (sections 1-20:
  architecture, sharding, recovery, retry, T+1 recon, kill switches)
- Topology visual DAG: `unified-trading-codex/04-architecture/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg`
- Error categories + retry policy SSOT: `unified-internal-contracts/schemas/errors.py` (ErrorCategory,
  ErrorRecoveryStrategy enums)
- Venue replay capabilities: `unified-api-contracts` per-venue schemas (Tardis 7yr, Databento 7yr, exchange 3mo REST,
  DeFi block replay)

6. **Done criteria**: Every task is "done" only after `quickmerge.sh` (full, not --unit-only) exits 0 AND no new errors
   in terminal output (see `runtime-verification-required.mdc`)
7. **No parallel code paths**: Delete old code after replacement — see `delete-deprecated.mdc`
8. **Versions**: All repos are 0.x.x until their tier is green on the new CI/CD pipeline. NEVER bump versions manually
   on branches. GitHub Action bumps on main merge only. Completion paths: CeFi/TradFi (primary) → DeFi (extension) →
   Sports (parallel post-commercialisation). See workspace-manifest.json completion_paths section for full required repo
   lists per path.

**Rename 6 repos (complete):** Tasks from rename_6_repos_consistency_328ed526.md are done. Repos renamed:
infra→ibkr-gateway-infra, alerting-service→alerting-service, client-reporting-api→client-reporting-api,
market-tick-data-handler→market-tick-data-service, execution-service→execution-service,
unified-api-contracts→unified-api-contracts. SVGs validated (xmllint OK). All UMI unified_api_contracts imports updated
to unified_api_contracts. Some venv installs and unit tests have pre-existing env/config issues
(unified-trading-services metadata, instruments-service GCP secrets). 9. **Progressive quickmerge** (use in order for
each tier):

- `--lint-only`: lint + format only (fastest feedback)
- `--unit-only`: lint + type check + unit tests (no integration, no act)
- `--qg-only`: full quality gates, no git ops (commit/PR)
- `--quick`: full QG + git ops, skip act
- (no flags): full validation including act — tier green only when this passes

---

## ⛔ Pre-flight Checklist — Fix Before Running Quickmerge

**These are BLOCKING quality gate violations. Quickmerge WILL fail if any are present.** **Fix them in any repo you
touch BEFORE running quickmerge --unit-only. No exceptions.**

Run this scan before touching code in any repo:

```bash
rg "os\.getenv\(" --type py --glob '!.venv*' --glob '!tests/**'      # must return 0 hits
rg "except\s*:" --type py --glob '!.venv*' --glob '!tests/**'        # bare except — must be 0
rg "except Exception\s*:" --type py --glob '!.venv*' --glob '!tests/**'  # bare Exception — must be 0
rg "getenv\(.*, \"\"\)" --type py --glob '!.venv*'                    # empty string fallback — 0
rg "getenv\(.*, \[\]\)" --type py --glob '!.venv*'                    # empty list fallback — 0
rg "getenv\(.*, \{\}\)" --type py --glob '!.venv*'                    # empty dict fallback — 0
rg "except ImportError" --type py --glob '!.venv*' --glob '!tests/**' # fallback imports — 0
```

| Violation                                                      | Rule                                                   | Fix                                                         |
| -------------------------------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------- |
| `os.getenv("KEY", "")` or `os.getenv("KEY")`                   | `no-empty-fallbacks.mdc`, `rule-amnesia-detection.mdc` | Use config class field or `os.environ["KEY"]` (fail loud)   |
| `except:` (bare)                                               | `strict-quality-gates.mdc` (E722 BLOCKING)             | Use specific exception type                                 |
| `except Exception: pass` or silent                             | `strict-quality-gates.mdc`                             | Log + reraise or use `@handle_api_errors`                   |
| `os.getenv("KEY", "")` / `config.x or ""`                      | `no-empty-fallbacks.mdc`                               | Pydantic required field or explicit `raise ValueError`      |
| `except ImportError: ...fallback...`                           | `delete-deprecated.mdc`                                | Fail loud — no try/except import fallbacks                  |
| File >900 lines                                                | `code-quality-limits.mdc` (BLOCKING)                   | Split by SRP — see `file-splitting-guide.md`                |
| Function >100 lines / method >50 lines                         | `code-quality-limits.mdc` (BLOCKING)                   | Extract helpers                                             |
| `from unified_config_interface import ConfigStore`             | `external-import-standards.mdc`                        | `from unified_trading_services import ConfigStore`          |
| `from unified_trading_services import InstrumentsDomainClient` | `instruments-domain-and-api-keys.mdc`                  | `from unified_domain_client import InstrumentsDomainClient` |
| `datetime.now()` / `datetime.utcnow()`                         | `utc-datetime.mdc`                                     | `datetime.now(timezone.utc)`                                |
| `# type: ignore` without bypass audit entry                    | `no-type-any-use-specific.mdc`                         | Fix root cause or add to `QUALITY_GATE_BYPASS_AUDIT.md`     |
| `Any` type annotation                                          | `no-type-any-use-specific.mdc` (BLOCKING)              | Use `TypedDict` / `Protocol` / specific type                |
| `central-element-323112` in test code                          | `single-project-id-env-var.mdc`                        | Replace with `test-project`                                 |
| Hardcoded project ID in source                                 | `no-hardcoded-project-ids.mdc`                         | Use `config.gcp_project_id`                                 |
| `print()` in source                                            | `anti-patterns-quick-reference.mdc`                    | `logger.info()`                                             |
| `List[x]`, `Dict[x,y]`, `Tuple[x]`                             | `builtin-generics-standard.mdc`                        | `list[x]`, `dict[x,y]`, `tuple[x]`                          |

**If you find any of the above in a file you are editing: fix it in the same commit.** **If you find it in a file you
are NOT editing but it's in the same repo: fix it too.** **Rationale: quickmerge runs quality gates across the entire
repo — one violation blocks the whole merge.**

---

todos:

- id: topology-ssot-index-update content: "Update unified-trading-codex/00-SSOT-INDEX.md with SSOT placement rationale
  (what governs = where it lives) and new entries for runtime-topology.yaml v6, venue replay capabilities, two-layer T+1
  reconciliation" status: pending
- id: topology-venue-replay-unified-api-contracts content: "Add venue replay capabilities table to unified-api-contracts
  (Tardis, Databento, per-exchange lookback/replay support, DeFi block replay) — referenced from runtime-topology.yaml"
  status: pending
- id: obs-event-required-fields content: "TIER 0: Add REQUIRED_EVENT_FIELDS dict to unified-internal-contracts/events.py
  — correlation_id, duration_ms, stack_trace, client_order_id per event category" status: done
- id: obs-audit-schema content: "TIER 0: Add audit.py schema to unified-internal-contracts/schemas/ — AuditRequirement,
  AuditRetention, EXECUTION_AUDIT (7yr), STRATEGY_AUDIT (3yr)" status: done
- id: topology-kill-switch-propagation content: "Implement kill switch propagation: deployment-api
  /kill-switch/{svc}/activate -> PubSub kill-switch-commands -> execution-service + strategy-service. Persist state in
  Secret Manager." status: pending
- id: topology-circuit-breaker-impl content: "Implement alerting-service circuit breaker command publishing:
  CIRCUIT_BREAKER_OPEN to PubSub circuit-breaker-commands topic, consumed by execution + strategy. Error-type-dependent
  reset." status: pending
- id: topology-with-retry-decorator content: "Implement @with_retry decorator in UTS based on unified-internal-contracts
  ErrorCategory + ErrorRecoveryStrategy. NETWORK=10 retries, VALIDATION=fail-fast, RATE_LIMIT=skip+resume." status:
  pending
- id: obs-perf-timing-helper content: "TIER 1: Implement @timed_operation decorator in UTS that auto-populates
  duration_ms in event metadata for COMPLETED events" status: pending
- id: obs-structured-error-context content: "TIER 1: Add stack_trace + error_category capture to UTS error handling
  (@handle_api_errors wraps stack trace into event metadata)" status: pending
- id: topology-timestamp-ordering content: "Implement exchange_timestamp + local_timestamp + sequence_number on all MTDH
  published messages. Gap detection triggers recovery. Consumer-side ordering support in UTS." status: pending
- id: topology-mdps-rolling-window content: "Implement MDPS ~1yr rolling candle window in Redis/memcached. Load from GCS
  on startup. Multi-timeframe update on natural boundaries." status: pending
- id: topology-t1-strategy-recon content: "Implement strategy T+1 reconciliation in strategy-validation-service: live
  signals vs batch-replayed, strategy PnL at benchmark fills." status: pending
- id: topology-t1-execution-recon content: "Implement execution T+1 reconciliation: live fills vs benchmark
  (TWAP/VWAP/arrival), execution alpha PnL. Aggregate with strategy T+1." status: pending
- id: topology-pbm-exchange-bootstrap content: "Implement PBM exchange position bootstrap: query exchange REST on
  startup, publish initial position snapshot to PubSub for strategy consumption." status: pending
- id: topology-features-mdps-event-chain content: "Wire features services to trigger on MDPS completion PubSub event
  instead of independent timers. Ensures features never run before MDPS finishes." status: pending
- id: obs-retention-ttls content: "DEPLOYMENT: Add retention TTLs to runtime-topology.yaml persistence_flows +
  data_retention_policy. Implement GCS lifecycle rules per dataset." status: done
- id: obs-health-probes content: "DEPLOYMENT: Add /health and /readiness endpoints to all API services
  (execution-results-api, market-data-api, client-reporting-api, deployment-api)" status: pending
- id: obs-checklist-items content: "DEPLOYMENT: Add phase_8 observability_compliance items (08a-08e) to
  checklist.template.yaml and propagate to service checklists" status: done
- id: topology-execution-order-lifecycle content: "Expand execution-service PubSub publishing from fills-only to full
  order lifecycle: ORDER_CREATED, ORDER_UPDATED, ORDER_CANCELLED, ORDER_FILLED, ORDER_REJECTED." status: pending
- id: obs-audit-trail-enforcement content: "SERVICE: Validate all execution events include client_order_id +
  exchange_timestamp, persisted to GCS audit/{client_id}/{date}/{event_type}/" status: pending
- id: obs-correlation-id-propagation content: "SERVICE: Wire correlation_id end-to-end: strategy -> execution -> PBM ->
  risk -> PnL -> client-reporting. Each hop adds local_timestamp." status: pending
- id: obs-pre-crash-checkpoint content: "SERVICE: Implement pre-crash state dump in ResourceAwareShutdownHandler —
  persist state to GCS at 85% memory threshold" status: pending
- id: obs-compliance-reporting-wiring content: "POST-REFACTOR: Wire T+1 recon output to MiFID/FCA reporting
  requirements. Map strategy T+1 to transaction reporting, execution T+1 to best execution (RTS 28)." status: pending
- id: manifest-topo-levels-fixed content: "DONE: Fix manifest topologicalOrder: UDC to L3, deployment-service/api to L5
  (later revised to L6 in tier-restructure 2026-02-28). WORKSPACE_MANIFEST_DAG.svg rebuilt." status: done
- id: checklist-templates-all-types content: "DONE: Create checklist templates for all component types:
  checklist.template.service.yaml, checklist.template.api-service.yaml, checklist.template.ui.yaml,
  checklist.template.library.yaml" status: done
- id: deployment-modes-topology content: "DONE: Add deployment_modes to runtime-topology.yaml: always_on, scale_to_zero,
  auto_scale, features_live" status: done
- id: ssot-index-updated content: "DONE: Update 00-SSOT-INDEX.md with 17 new SSOT entries + placement principle" status:
  done
- id: dag-ml-inference-bigquery-to-pubsub content: "ML inference reads features from BigQuery (polling) not PubSub.
  Needs refactoring to PubSub subscription for live features per architectural decisions." status: pending
- id: dag-ml-inference-remove-training-dep content: "Remove ml-training-service from ml-inference-service pyproject.toml
  dependency. Both should share code via unified-ml-interface only (DAG violation V4)." status: pending
- id: dag-instruments-pubsub-all-consumers content: "Add instruments-service PubSub subscription to ALL downstream
  consumers (features, strategy, execution) not just MTDH/MDPS. All services need instrument adds/removes/status live."
  status: pending
- id: dag-features-calendar-onchain-pubsub content: "Add PubSub publish for features-calendar-service and
  features-onchain-service. Keep architecture uniform even for infrequent services. Run on ~15min timer aligned to UTC."
  status: pending
- id: dag-strategy-subscribe-features content: "Enable strategy-service to optionally subscribe to feature PubSub topics
  (calendar events, delta-one features). Config-driven subscription." status: pending
- id: dag-execution-subscribe-features content: "Enable execution-service to optionally subscribe to features-delta-one
  PubSub (VWAP, HFT features for smart algos). Config-driven subscription." status: pending
- id: hft-features-deployment content: "HFT Features Deployment: Fix 15 import errors from test run, install
  hmmlearn/ruptures/scipy in affected repos, provision API keys (Databento, CryptoPanic, LunarCrush, CryptoQuant, FRED)
  in Secret Manager, create PubSub topics for features-cross-instrument-service, deploy
  features-cross-instrument-service + updated services (MDPS, features-delta-one, features-volatility,
  market-tick-data-service, features-calendar, features-onchain), backfill 2024 data, validate schemas. See
  unified-trading-pm/HFT_FEATURES_MIGRATION_GUIDE.md for complete spec. Implementation complete (local), 27 features
  across 5 tiers, 70%+ test coverage, all SSOTs updated." status: pending priority: P1 blocked_by: "Testing
  infrastructure (integration-testing-layers)"
- id: dag-shared-dimensions-schema content: "Add shared dimension schema to unified-internal-contracts: client, account
  (not subaccount), venue, instrument, underlying, risk_category, strategy_id, pool. Used by PBM, risk, PnL." status:
  pending
- id: dag-account-rename-subaccount content: "Rename 'subaccount' to 'account' across execution-service,
  runtime-topology.yaml, sharding configs. Account ID = venue + account_type + sequence." status: pending
- id: dag-rate-limit-tracker content: "Implement persistent rate limit tracker in execution-service using
  VenueRateLimiter from UMI. Track usage per venue, persist to Redis to survive restarts, respect daily/hourly limits."
  status: pending
- id: dag-subscription-mgmt-ssot content: "Define SSOT for runtime subscription config: which service subscribes to
  which PubSub topics. Config-driven, changeable via onboarding-ui. Propagates via PubSub events from
  internal-contracts." status: pending
- id: dag-ufc-moved-to-l0 content: "DONE: Removed unused unified-cloud-interface dep from UFC pyproject.toml. Moved UFC
  to Level 0 (pure math, zero unified-\* deps). Updated manifest + SVG + mermaid DAG." status: done
- id: dag-udei-moved-to-l2 content: "DONE: Removed false UMI dependency from UDEI in manifest. Moved UDEI from L4 to L2
  alongside UTEI. Renumbered all levels (9 total: L0-L8)." status: done
- id: dag-venue-interface-plan content: "L0 LIBRARY: Create unified-venue-interface at L2 providing
  BaseVenueExecutionAdapter protocol, VenueCapabilities model, shared venue auth + order rate limiting. UTEI/UDEI/USEI
  extend this base." status: pending
- id: dag-udei-enhance-defi content: "L2 LIBRARY: Enhance unified-defi-execution-interface with full DeFi protocol
  coverage: Uniswap v3 router, Aave v3 lending pool, Morpho Blue, Lido stETH, gas estimation, atomic tx patterns."
  status: pending
- id: dag-ibkr-infra-testing content: "L0 INFRA: Complete IBKR Gateway Terraform config in ibkr-gateway-infra/ repo.
  Wire auth testing for IBKR venue adapter. May need human input for credentials." status: pending
- id: dag-checklist-propagation content: "DEPLOYMENT: Propagate checklist.template.{service,api-service,ui,library}.yaml
  to all 55 repos. Generate per-repo checklist from appropriate template based on manifest type field." status: pending
- id: p0-exec-results-api-types content: execution-results-api — replace all dict[str, Any] at API boundaries with
  TypedDict/Pydantic response models status: pending
- id: p0-ml-bare-except content: "ml-training-service/cli/main.py:212,218,299 — replace bare except Exception: pass with
  proper logging + reraise" status: pending
- id: p0-strategy-live-mode content: "strategy-service — add live mode seams: live_data_source.py (Pub/Sub subscriber) +
  broadcast_sink.py (Pub/Sub publisher); engine stays mode-agnostic" status: pending
- id: p0-cdc-tests content: Create unified-internal-contracts/tests/consumer_tests/ — CDC tests for key
  producer→consumer pairs status: pending
- id: p0-umi-skipped-test content: Unskip skipped test in unified-market-interface/tests/ — depends on
  canonical-swap-fix (p0-canonical-swap-fix) status: pending
- id: p0-canonical-swap-fix content: Bump UIC patch version + reinstall in UMI — CanonicalSwap stale installed package
  status: pending
- id: p0-ui-sse content: Add SSE endpoints (sse-starlette) to execution-results-api + health-monitor-api; wire
  live-health-monitor-ui and trading-analytics-ui as SSE clients; populate shell UIs status: pending
- id: p0-reportany-error-all-repos content: Upgrade reportAny from 'warning' to 'error' in ALL 17 repos. Update
  pyproject.toml + pyrightconfig.json. Fix all Any-type violations. status: pending
- id: auth-credentials-registry content: "PARTIAL — execution-service/configs/credentials-registry.yaml EXISTS
  (exec-services client→SM secret mapping only). Remaining: expand to system-wide
  unified-trading-pm/credentials-registry.yaml covering ALL services + secret types (API keys, GCP SA, OAuth, DB); add
  status (active/pending/missing) per secret; add setup guide per type." status: partial
- id: auth-setup-secret-script content: Generalize market-tick-data-handler/scripts/setup-secret-manager.sh →
  unified-trading-pm/scripts/setup_secret.sh with --name, --project-id, --from-json args status: pending
- id: auth-secret-manager-naming content: Enforce canonical Secret Manager naming in all config files; update existing
  binance-api / deribit-api refs; add cursor rule secret-naming.mdc status: pending
- id: auth-three-tranche-data-wiring content: "Wire tranche_router.py: Tranche A (manual CSV), Tranche B (Secret Manager
  exec-odum-{venue}-{account_type}), Tranche C (position-balance-monitor + pnl-attribution APIs)" status: pending
- id: auth-ai-report-summaries content: "Add ai_summary.py: anthropic claude-3-5-haiku for executive summaries; API key
  via Secret Manager anthropic-api-key" status: pending
- id: auth-onboarding-ui-gaps content: "Complete onboarding-ui: AMLScreening, FeeStructureConfig, HWMInitialization,
  APIKeyManagement (Secret Manager exec-odum-{venue}), AuditLog, VenueOnboarding, StrategyOnboarding — Google OAuth
  ADMIN" status: pending
- id: auth-onboarding-ui-complete content: Complete onboarding-ui client creation wizard, API key CRUD with Secret
  Manager backend wired to credentials-registry.yaml, connection test, strategy-account mapping status: pending
- id: auth-manual-trading-consolidate content: Consolidate manual trading to live-health-monitor-ui; add submitted_by
  (OAuth), reason, cancel/amend endpoints status: pending
- id: auth-trading-analytics-ui content: "Build trading-analytics-ui: Google OAuth TRADER, /positions, /pnl,
  /executions, /risk, /orderbook, /latency" status: pending
- id: auth-config-promotion-workflow content: Wire BacktestGridResult → StrategyConfig promotion. POST
  /api/v1/config/promote, ConfigStore, deployed_by from OAuth status: pending
- id: auth-ml-training-ui content: "Build ml-training-ui as ML Analytics & Deployment: /experiments,
  /experiments/:runId/deploy, /models, Google OAuth" status: pending
- id: auth-deployment-service-split content: "Refactor unified-trading-deployment-v3: extract config_service.py, add
  Google OAuth to auth_middleware" status: pending
- id: deployment-v3-four-way-split content: > Split unified-trading-deployment-v3 into 4 repos (shared-config dissolved
  — schemas in AC/UIC, configs in deployment-service): (1) deployment-service/ — Python package (orchestrator, catalog,
  config_loader, cli, cloud_client, monitor, shard_builder, shard_calculator, backends/), terraform/, configs/ (YAML
  checklists, bucket configs). Move smoke_test_framework.py → tests/integration/shard_smoke/. Split orchestrator.py
  (672L) and config_loader.py (551L) by SRP before extract. (2) deployment-api/ — thin FastAPI (api/ from UTD V3);
  imports deployment-service; GoogleOAuthMiddleware on write endpoints; port 8001. (3) deployment-ui/ — React UI calling
  deployment-api; OAuth ADMIN scope for trigger buttons; SSE for status. (4) system-integration-tests/ — NEW repo (per
  new-repo-setup.md). Layer 3a (fast smoke) + Layer 3b (full pipeline smoke). Sequential: 3a must pass before 3b.
  Triggered by deployment-api post-deploy. Layer 2 (infra verification) lives in
  deployment-service/scripts/verify_infra.py — gates deployment success before Layer 3. SSOT:
  unified-trading-/codex/06-coding-standards/integration-testing-layers.md status: pending
- id: auth-ibkr-corp-actions content: "P1: Implement URDI IBKR corporate actions adapter using
  ib_insync.CorporateAction; mark PENDING_CASSETTE_AWAITING_AUTH" status: pending
- id: auth-endpoint-registry-unvalidated content: "NOT IN CODEBASE YET — endpoint_registry.py only has requires_auth:
  bool, no cassette/validation status. Design+implement: (1) Add CassetteStatus(StrEnum): VALIDATED,
  BLACKLISTED_NO_AUTH, BLACKLISTED_NO_API, AWAITING_CASSETTE, PUBLIC_NO_CASSETTE; (2) Add cassette_status +
  cassette_reason fields to EndpointSpec; (3) Backfill all 22+ auth-required venues in ENDPOINT_REGISTRY; (4) This
  becomes SSOT for why a venue has no VCR test — referenced by CI and schema-contract-validation plan." status: pending
- id: auth-sports-migration-batch1 content: "Sports migration Phase 1+2: auth status fixes in endpoint_registry + UIC
  sports canonical schemas (fixture, events, xg, odds, weather, reference)" status: pending
- id: auth-sports-migration-batch2 content: "Sports migration Phase 3+4: UMI adapter completions for sports venues +
  features-sports-service creation" status: pending
- id: lib-phase1-udc-tier2-compliance content: "UDC: replace CloudTarget/get_config/market_category imports from UCS
  with UCLI equivalents; remove unified-trading-services from UDC pyproject.toml; add
  unified-cloud-interface>=1.0.0,<2.0.0" status: pending
- id: lib-phase1-uts-domain-cleanup content: "UTS: remove create_instruments_client, create_market_candle_data_client,
  StandardizedDomainCloudService re-export from **init**.py; services import from UDC only" status: pending
- id: lib-phase2-uts-rename-step1 content: "UTS Step 1: add unified_trading_services/ re-export package; update
  pyproject.toml for dual publish; update workspace-manifest.json; update cursor rules + codex docs" status: pending
- id: lib-phase2-udc-rename-step1 content: "UDC Step 1: add unified_domain_client/ re-export package; update
  pyproject.toml for dual publish; update workspace-manifest.json" status: pending
- id: lib-phase2-rename-step2 content: "Phase 2 Step 2: update all 14 services + Tier 2 libs to use new import names;
  remove aliases; rename GitHub repos + Artifact Registry packages + Cloud Build triggers" status: pending
- id: lib-phase3-urdi-setup content: "URDI is TIER 0 per canonical DAG (was mislabelled Tier 2 in this plan). Harden as
  Tier 0 leaf: verify REST adapters exist for major venues; API keys via get_secret_client inside adapter; rate limiting
  via UMI VenueRateLimiter; retry via UTS @with_retry; quality-gates.sh/quickmerge.sh/pyrightconfig.json present; update
  workspace-manifest arch_tier=0." status: pending
- id: lib-phase3-instruments-service-urdi-wire content: "Wire instruments-service to URDI: replace direct exchange REST
  calls with get_reference_adapter(venue).get_instruments()" status: pending
- id: lib-phase4-connectivity-audit content: "Audit all 14 services: verify zero os.getenv('API_KEY'), hardcoded URLs,
  direct requests/aiohttp to venues. All connectivity via UDC/UMI/UTEI/URDI." status: pending
- id: lib-phase5-t1-quality-gates content: "UTS quality gates: uv pip install -e .[dev]; bash scripts/quality-gates.sh;
  fix all failures; quickmerge" status: pending
- id: lib-phase5-t2-quality-gates content: "T2 quality gates (3 parallel agents): UDC+UMI, UTEI+UML, UFC+UPI —
  per-library QG checklist; MIN_COVERAGE=70; no Tier 2 importing from Tier 1; quickmerge each. NOTE: URDI is Tier 0 (not
  T2) — its QG is handled in T0 STEP A." status: pending
- id: lib-phase6-service-code-adjustment content: "14 services (4 parallel agents): update import names post-rename;
  remove direct cloud deps from pyproject.toml; verify setup_service(sink=GCSEventSink(...))" status: pending
- id: lib-phase7-instruments-service-validation content: "instruments-service validation gate: uv pip install -e .[dev];
  quality-gates.sh; verify imports from unified_trading_services + unified_domain_client; document patterns for
  remaining 13 services" status: pending
- id: vcr-public-venues content: "VCR cassettes + replay tests for 8 public/no-auth venues: kalshi, polymarket,
  thegraph, defillama, barchart, open_meteo, upbit, fear_greed" status: pending
- id: vcr-urdi-parse-raw-umi-stubs content: Add abstract \_parse_raw to URDI base_adapter; implement 12
  NotImplementedError stubs in UMI (coinbase, databento, tardis, aster normalizers) status: pending
- id: vcr-execution-results-api-uic content: "Full UIC adoption for execution-results-api: EnhancedError on all
  exception handlers, lifecycle log_events, typed Pydantic response models" status: pending
- id: vcr-new-adapters-public content: "New UMI adapters group 1 (public/VCR-testable): kalshi, polymarket, defillama,
  fear_greed" status: pending
- id: vcr-new-adapters-cefi-sports content: "New UMI adapters group 2 (auth-required, BLACKLISTED_UNVALIDATED): aster,
  upbit, odds_api, pinnacle, glassnode, arkham" status: pending
- id: vcr-new-adapters-tradfi-altdata content: "New UMI adapters group 3: ibkr, fred, ecb, ofr, openbb, yahoo_finance,
  api_football, footystats, soccer_football, mev; delete empty defi/schemas.py; blacklist github" status: pending
- id: vcr-enhanced-error-high-priority content: "Replace 311 bare excepts with EnhancedError: execution-service (201),
  instruments-service (62), market-tick-data-service (48)" status: pending
- id: vcr-enhanced-error-remaining content: "EnhancedError rollout: features-delta-one (20), features-onchain (13),
  features-volatility (12); remove unified-position-interface from .cursorignore" status: pending
- id: vcr-quality-gates content: Run quality gates on unified-api-contracts, UMI, URDI to verify all new VCR tests and
  adapters pass status: pending
- id: ac-exhaustive-schema-universe content: | unified-api-contracts must be EXHAUSTIVE for every venue/data source in
  our universe — not placeholder-complete or partial. Current state: many schemas are stubs, several venues have zero
  raw schemas, normalised schemas miss whole method families. Required coverage per source category: CeFi exchanges
  (raw + normalised): Binance (spot+perp+options), OKX (spot+perp+options), Deribit (options+perp), Bybit
  (spot+perp+options), Hyperliquid (perp+spot), Coinbase (spot), Aster (spot+perp), Upbit (spot), IBKR
  (equities+options+futures+forex). Method families per CeFi venue: orderbook, trades, klines/ohlcv, ticker, mark_price,
  index_price, funding_rate (history+predicted), open_interest (history), liquidations, insurance_fund, position_risk,
  order (create/amend/cancel/list), fills, balance, transfer, withdraw, deposit, sub_account, portfolio_margin_mode,
  vol_surface (options venues), greeks, settlement_history. DeFi protocols (raw + normalised): Uniswap v3/v4, Aave v3,
  Curve, Hyperliquid DEX. Method families: pool_state, swaps, positions, liquidity, yields, liquidations, LTV.
  Reference/alt data (raw + normalised): Tardis (multi-venue normalised feed schemas), Databento (MBP-10, MBO, OHLCV,
  Trades, Status), Kalshi (contracts, orderbook, fills), Polymarket (markets, orderbook, fills), TheGraph (queries for
  Uniswap/Aave/Curve), DeFiLlama (protocol TVL, yields, chains), Glassnode (on-chain metrics), Arkham (entity labels,
  flows), FRED (macro series), ECB (rates), OFR (financial stability data), Fear&Greed index, Open Meteo (weather for
  sports), api_football, FootyStats, soccer-football-info. Each venue must have: (1)
  unified_api_contracts_external/{venue}/schemas.py — raw API response shapes; (2)
  unified_normalised_contracts/{category}/schemas.py — canonical normalised shape; (3) VCR cassette OR CassetteStatus
  marking (VALIDATED/AWAITING_AUTH/BLACKLISTED_NO_AUTH/etc.); (4) at least one round-trip test (raw→normalised transform
  test). Placeholder/stub schemas must be replaced before any consumer service can be considered complete. status:
  pending
- id: ac-ccxt-completeness content: "Expand ccxt/schemas.py to ~90% CCXT surface: ~50 method schemas; expand
  CcxtPosition/Order/Market/Balance/Ticker/Trade" status: pending
- id: ac-fee-borrow-all-venues content: Add fee and borrow rate schemas across Binance, Bybit, OKX, Deribit, IBKR, Aster
  status: pending
- id: ac-risk-infrastructure content: Add InsuranceFund, AdlQuantile, RiskLimit, PositionRisk schemas across venues
  status: pending
- id: ac-funding-settlement-portfolio-margin content: Add funding rate history REST, settlement, portfolio margin
  schemas status: pending
- id: ac-sentiment-oi-all-venues content: Add L/S ratio, OI history, buy/sell volume schemas across venues status:
  pending
- id: ac-account-lifecycle-all-venues content: Add deposit/withdrawal/transfer/sub-account schemas (100% missing across
  venues) status: pending
- id: ac-aggregate-trades-fills-mark-price content: Add AggTrade, MyTrades, MarkPriceKline, IndexPriceKline across
  venues status: pending
- id: ac-vol-surface-all-venues content: "Add vol surface schemas: Deribit DVOL, OKXOptionSummary, canonical
  VolatilitySurface" status: pending
- id: ac-shared-schema-extensions content: Extend schemas/derivatives.py and schemas/accounts.py with canonical forms
  status: pending
- id: ac-dual-structure-doc content: Document consolidation plan for unified_api_contracts_external/ vs top-level dirs;
  ensure no duplicate import paths status: pending
- id: ac-coverage-90 content: Raise unified-api-contracts test coverage from 70% to 90% in pyproject.toml status:
  pending
- id: ac-restructure content: "Restructure unified-api-contracts: unified_api_contracts_external/ +
  unified_normalised_contracts/" status: pending
- id: ic-unified-internal-repo content: Create unified-internal-contracts repo with full setup (pyproject.toml,
  quality-gates.sh, quickmerge.sh) status: pending
- id: ic-client-account-domain-model content: "Create unified_internal_contracts/client/entities.py: Client,
  VenueAccount, Strategy, ClientAccountMapping" status: pending
- id: ic-greeks-position-schema content: "Create unified_internal_contracts/positions/greeks.py: GreeksExposure (delta,
  gamma, theta, vega, rho, delta_notional_usd, underlying)" status: pending
- id: ic-pnl-breakdown-schema content: "Create unified_internal_contracts/pnl/breakdown.py: PnLBreakdown with
  instrument_id, instrument_type, underlying, asset_group, delta_pnl, basis_pnl, funding_pnl, greeks_pnl dimensions"
  status: pending
- id: ic-pnl-attribution-complete content: "Complete pnl-attribution-service: delta PnL, funding rate PnL, basis PnL,
  interest rate PnL, Greeks PnL (options), mark-to-market vs realized, 6-dimension breakdown" status: pending
- id: ic-risk-service-complete content: "Complete risk-and-exposure-service: VaR, portfolio Greeks aggregate, DeFi LTV,
  CeFi margin health, circuit breaker triggers" status: pending
- id: ic-rebalance-instruction content: "P1: Create unified_internal_contracts/strategy/rebalance.py:
  RebalanceInstruction with target_weights, rebalance_type, deviation_threshold" status: pending
- id: ic-circuit-breaker-schema content: "P1: Create unified_internal_contracts/events/circuit_breaker.py:
  CircuitBreakerEvent (state OPEN/CLOSED/HALF_OPEN, trigger type, threshold vs observed)" status: pending
- id: ic-eod-settlement-contract content: "P1: Create unified_internal_contracts/settlement/eod.py:
  EODSettlementTrigger; add EOD_SETTLEMENT topic to pubsub.py" status: pending
- id: ic-feature-contracts content: "P1: Create unified_internal_contracts/features/: FeatureStalenessConfig,
  FeatureDriftAlert, FeatureParityReport schemas" status: pending
- id: ic-ml-training-contracts content: "P1: Create unified_internal_contracts/ml/training.py: CrossValidationResult,
  ModelDegradationAlert; ml/drift.py: PredictionDriftAlert" status: pending
- id: ic-uic-coverage-floor content: "P1: Raise UIC test coverage from 35% to 80%; add tests for client/, features/,
  regulatory/, positions/greeks.py" status: pending
- id: ic-uic-py-typed content: "P1: Add empty py.typed to unified-internal-contracts/unified_internal_contracts/; update
  pyproject.toml package-data" status: pending
- id: ic-strategy-domain-event-validation content: "P1: strategy-service/domain_events.py — wrap all event constructors
  in Pydantic model_validate" status: pending
- id: ic-portfolio-risk-contracts content: "P2: Create unified_internal_contracts/risk/portfolio.py: PortfolioVaR
  (component VaR, correlation hash), PortfolioAllocation" status: pending
- id: ic-onchain-freshness-contract content: "P2: Create unified_internal_contracts/features/onchain_freshness.py:
  OnchainDataFreshnessConfig per chain (max_block_lag, max_age_seconds)" status: pending
- id: ic-onchain-per-protocol-schemas content: "P2: features-onchain-service — add protocol-discriminated feature output
  schemas: AaveFeatureOutput, UniswapV3FeatureOutput, CurveFeatureOutput" status: pending
- id: ic-trad-fi-datasource-tag content: "P2: Add data_source_constraint field to InstrumentRecord; tag all Trad-Fi
  instruments as DATABENTO_ONLY" status: pending
- id: ic-deprecated-withdraw-cleanup content: "P2: unified-domain-client — remove deprecated WITHDRAW instruction type
  and signal_id field (delete-deprecated.mdc compliance)" status: pending
- id: ui-orderbook-viz content: "Build /orderbook page in trading-analytics-ui: OrderBookDepthChart, OrderBookTable,
  TradeTimeline, SSE from market-data-api" status: pending
- id: ui-latency-plots content: "Build /latency page: ExecutionLatencyHistogram, SlippageScatter, GatewayRoundtrip,
  P50/P95/P99 table" status: pending
- id: ui-system-health-page content: "Build /system-health in live-health-monitor-ui: ServiceStatusGrid,
  CPUMemoryTimeSeries, PubSubLagBars, DLQDepthBadges, Active Alerts SSE" status: pending
- id: ui-skeleton-assess content: Assess execution-analytics-ui, client-reporting-ui, settlement-ui — what data schemas
  they need vs what's available; scope SSE integration status: pending
- id: arch-ui-separation-rule content: "MISSING RULE: No cursor rule or codex states UI is always a separate repo from
  its service. Create .cursor/rules/ui-service-separation.mdc: UI code (React/TS, package.json, node_modules) must NEVER
  live inside a service repo. Every UI is its own repo. Services expose HTTP (FastAPI) + OAuth; UIs consume them.
  Building a new UI repo to complete a feature is correct and expected." status: pending
- id: arch-exec-services-visualizer-extract content: "ACTIVE VIOLATION: execution-service/visualizer-ui/ is a full React
  app (Dockerfile, package.json, playwright) inside a Python service. execution-service/visualizer-api/ is a standalone
  FastAPI inside the same repo. Extract: (1) visualizer-ui/ -> new repo execution-visualizer-ui; (2) visualizer-api/ ->
  merge into execution-results-api or new execution-visualizer-api repo; (3) delete both dirs from execution-service;
  (4) update cloudbuild.yaml." status: pending
- id: arch-deployment-v3-ui-extract content: "ACTIVE VIOLATION: unified-trading-deployment-v3/ui/ is React co-located
  with FastAPI backend. Extract to new repo deployment-ui. Backend = pure FastAPI + OAuth. deployment-ui consumes
  backend via HTTP + SSE. This supersedes auth-deployment-service-split — the split is a full repo separation, not just
  route extraction." status: pending
- id: ui-service-separation-audit-full content: "Full audit of all service repos for embedded UI: check for ui/,
  frontend/, static/, visualiz*, *.tsx, \*.jsx, package.json, index.html inside Python service repos. Known violations:
  execution-service (visualizer-ui + visualizer-api), unified-trading-deployment-v3 (ui/). Check also: alerting-service,
  market-data-processing-service, client-reporting-api, risk-and-exposure-service." status: pending
- id: ui-ml-training-config-wire content: Wire MLTrainingConfig UIC into ml-training-service. ConfigStore,
  MLTrainingResult status: pending
- id: obs-metrics-aggregator-api content: "Add GET /api/system/metrics to alerting-service: fan-out to Prometheus
  endpoints, parse, cache 15s" status: pending
- id: obs-grafana-export content: Export Grafana dashboards (trading-overview.json, system-health.json), provisioning,
  SimpleJSON datasource status: pending
- id: obs-prometheus-codex content: "Create unified-trading-/codex/03-observability/prometheus-metrics.md: metric
  catalog, alert rules, service map, triage guide" status: pending
- id: quality-importerror-fallbacks content: Fix except ImportError fallbacks (~130 files) status: pending
- id: quality-large-file-splits content: "Split large files: engine.py (2826L), aws_schemas.py (1424L),
  venue_manifest.py (1058L), binance/schemas.py (1033L)" status: pending
- id: quality-type-ignore-arch-violations content: Fix 67 architectural type:ignore violations status: pending
- id: test-mock-framework content: "Build unified-testing-library: ModelFactory (polyfactory for Pydantic fixtures),
  MockGCSClient, MockPubSubClient, MockSecretManagerClient, MockIBKRGateway" status: pending
- id: test-e2e-smoke-tests content: "End-to-end offline smoke tests: fixture generator → normalize → GCS mock write →
  feature compute → strategy signal → execution mock" status: pending
- id: dag-tier-corrections content: "Fix tier numbering across plan, codex, workspace-manifest, and cursor rules to
  match canonical DAG: URDI=Tier0 (was T2 in plan lib-phases); UDC=Tier3 (manifest says T2 — codex+DAG override; add
  manifest note); EAL=Tier0; MEL=Tier2. Update lib-phase descriptions: lib-phase3 (URDI) is Tier 0 hardening, not
  Tier 2. Update workspace-manifest.json arch_tier fields for URDI (0), UDC (3), EAL (0)." status: pending
- id: dag-orphan-repos-manifest content: "⚠️ DAG flags 4 orphan repos not in workspace-manifest.json:
  execution-results-api, market-data-api, client-reporting-api, strategy-ui. Add all 4 to workspace-manifest.json with
  correct type (apiSvc or ui), arch_tier, dependencies, cloud_build_trigger, and status fields. These are real
  deployed/in-progress repos, not future." status: pending
- id: dag-uts-v22-feature-audit content: "DAG shows UTS v2.2 has: ConfigStore, GCSEventSink, PubSubEventSink,
  QueueEventSink, ServiceCLI, BatchOrchestrator, @with_retry, setup_service, StateStore, BaseCloudWriter,
  GracefulShutdownHandler. Audit which of these are actually implemented vs declared. lib-phase1 (UTS domain cleanup)
  and lib-phase5 (QG) may be ahead of/behind this. Update plan phases to only do work that isn't already done." status:
  pending
- id: dag-batch-live-message-buses content: "DAG canonically defines: GCS = batch message bus (Parquet files); Cloud
  Pub/Sub = live event bus (MessagingScope: CROSS_VM); Redis = hot order state (MessagingScope: SAME_VM). Ensure: (1)
  all service batch schemas produce/consume Parquet via UDC; (2) all live schemas produce/consume Pub/Sub events via UTS
  PubSubEventSink/QueueEventSink; (3) contract smoke test service-pairs.yaml uses batch_schema_class (Parquet schema)
  and live_schema_class (Pub/Sub event schema) per DAG edges; (4) MessagingScope enum is enforced in
  unified-internal-contracts." status: pending
- id: dag-service-pairs-derivation content: "service-pairs.yaml (e2e-service-pair-registry) can be directly derived from
  DAG edges. Service data flows per DAG: MTDH --(batch write GCS)--> MDPS; MTDH --(live publish PS)--> FDS/FVS/STR/MLIN;
  GCS --(batch read)--> FCS/FDS/FVS/FOS/MLTR/MLIN/STR/EXEC; PS --(live subscribe)--> FDS/FVS/STR/MLIN; EXEC --(batch
  write)--> ERA; MTDH/MDPS --(batch write)--> MDA. Also: IS uses URDI+UMI+UDC; EXEC uses UTEI+EAL+UMI+UDC. Populate from
  these 40+ edges." status: pending
- id: dag-api-services-cluster content: "DAG defines an 'API Services' cluster (FastAPI+SSE) separate from Services
  cluster: ERA (execution-results-api), MDA (market-data-api), CRA (client-reporting-api). These are the HTTP boundary
  between services and UIs — NOT the same as service engine code. Confirm: each has its own repo, no service engine
  code, FastAPI only, OAuth middleware. ERA has P0 dict-Any fix (p0-exec-results-api-types). MDA is new repo (was in
  monitoring plan). Update plan todos to reference this cluster explicitly." status: pending
- id: cohesion-umi-udc-dep-violation content: "TIER VIOLATION: workspace-manifest.json lists unified-domain-client as a
  dep of unified-market-interface (T2→T3 lateral import). T2 must only import T0+T1. Remove UDC from UMI pyproject.toml
  deps. Any UDC functionality UMI uses must be sourced from T0 (UCLI/UCI/AC) or T1 (UTS). Audit UMI source for any from
  unified_domain_client imports and eliminate. Add tier-boundary CI check to UMI quality-gates.sh." status: pending
- id: cohesion-uic-int-unified-api-contracts-dep content: "MANIFEST GAP: workspace-manifest.json has
  unified-internal-contracts with dependencies: [] (empty). schema-ownership plan requires it to import
  unified-api-contracts (for normalised contract schemas used in MessagingTopic, EventEnvelope). Add
  unified-api-contracts as dep in unified-internal-contracts pyproject.toml and manifest entry. Verify
  ic-unified-internal-repo todo (ic-\*) picks this up — add explicit dep wiring step." status: pending
- id: cohesion-upi-pbm-dependency content: > PARTIAL (2026-02-28): (1) UPI → PBM edge added to TOPOLOGY-DAG.md in codex.
  (2) PBM pyproject.toml already had unified-position-interface dep. (3) Added CanonicalPosition import to
  position_tracker.py; added to_canonical(position) method converting local Position → CanonicalPosition (mark_price
  placeholder — callers must update from live market data before publishing externally). (4) Created missing UIC
  position submodules (see ic-uic-positions-modules-done). Remaining: UPI adapters (CCXT, OKX, IBKR) feed PBM reader
  seam; lib-phase5-t2-quality-gates must include UPI. status: partial
- id: ci-manifest-status-fields content: "SSOT GAP: workspace-manifest.json status field is NO_STATUS for 40/45 repos —
  no ci_status, quality_gate_status, testing_level, or bypass_audit fields exist. Add per-repo fields: ci_status
  (green/red/no_ci), quality_gate_status (passing/failing/not_run), coverage_pct (last known), bypass_audit_path,
  testing_level (none/unit/integration/e2e), skipped_gates (list of intentionally skipped checks with reason)." status:
  pending
- id: ci-quality-gates-missing-repos content: "12 repos have cloudbuild.yaml but NO quality-gates.sh:
  unified-api-contracts, unified-events-interface, unified-reference-data-interface, alerting-service,
  unified-trade-execution-interface, features-calendar-service, unified-position-interface, unified-trading-services,
  ml-training-service, ml-inference-service, client-reporting-api, pnl-attribution-service. Add quality-gates.sh from
  codex template (06-coding-standards/quality-gates-library-template.sh or service template) to each." status: pending
- id: ci-bypass-audit-missing-repos content: "QUALITY_GATE_BYPASS_AUDIT.md exists at workspace root + ~10 repos. 20+
  repos with quality-gates.sh have NO per-repo bypass audit. Create QUALITY_GATE_BYPASS_AUDIT.md in every repo that has
  quality-gates.sh; run quality gates, document all # type: ignore suppressions with category + reason. Repos confirmed
  missing: all those with quality-gates.sh but no bypass audit file." status: pending
- id: ci-quality-gates-alignment content: "No SSOT check that all repos use the same ruff/basedpyright/coverage
  settings. Audit: (1) ruff rules alignment — are all repos using the same rule set from codex template? (2)
  basedpyright strictness — is reportAny=warning or error consistent? (3) MIN_COVERAGE floor — is 70% (libraries) / 35%
  (services) enforced in all pyproject.toml? (4) pip-audit + bandit — present in all dev deps? Add
  cicd_status_validator.py enforcement to workspace CI." status: pending
- id: ci-arch-violations-fix content: "67 ARCHITECTURAL_VIOLATION type: ignore suppressions in
  QUALITY_GATE_BYPASS_AUDIT.md — must fix, not suppress. Key clusters: execution-service (params: Any, dict[str,Any]
  boundaries), unified-defi-execution-interface (union not narrowed), unified-trading-deployment-v3 (arg-type
  compute_type). These are separate from the p0-reportany-error-all-repos task which is about turning reportAny to
  error; these are existing suppressions already failing architectural standards." status: pending
- id: ci-per-repo-status-run content: Run quality gates on all 30 repos that have quality-gates.sh; record pass/fail +
  coverage % + bypass count per repo into workspace-manifest.json ci_status fields (ci-manifest-status-fields). Use 4
  parallel agents (8 repos each). This is the baseline snapshot needed before any hardening work can be tracked. status:
  pending
- id: ci-cloudbuild-quality-gate-wire content: "Verify all 29 cloudbuild.yaml files actually invoke quality-gates.sh
  inside the Docker image (not just run pytest standalone). Per cloud-build-test-in-image.mdc: tests run INSIDE the
  built image. Audit each cloudbuild.yaml for the pattern: docker build → docker run quality-gates.sh --no-fix --quick →
  docker push. Fix any that run pytest or ruff outside the image." status: pending
- id: e2e-contract-smoke-framework content: | SUPERSEDED BY integration-testing-layers.md. Layer 0 (AC↔UIC alignment) →
  integration-layer0-ac-uic-\* todos in T0. Service-pair schema alignment → integration-layer3-implement (Layer 3a in
  system-integration-tests). Keep this todo for traceability; mark completed when Layer 0 + Layer 3a implemented.
  status: superseded
- id: e2e-auth-config-smoke content: | Build auth_smoke_test.py in
  unified-trading-deployment-v3/unified_trading_deployment/. No running services needed — validates auth config
  completeness for every service: (1) local: .env.example has all required vars, Secret Manager secret names match
  credentials-registry.yaml; (2) GitHub workflow: GOOGLE_APPLICATION_CREDENTIALS secret present in workflow env; (3)
  Cloud Build (GCP): service account has correct IAM roles per checklist.\*.yaml; (4) AWS: CLOUD_PROVIDER=aws path has
  matching secret names in AWS Secrets Manager convention (cloud-agnostic-migration.md); (5) inter-service auth: each
  service pair that communicates has auth config defined (local SA, mTLS spec, or OAuth). Runs in: local dev (python -m
  pytest tests/smoke/), GitHub workflow, Cloud Build step. status: pending
- id: e2e-smoke-github-workflow content: "Add .github/workflows/contract-smoke.yml to unified-trading-deployment-v3:
  triggers on push to main and PR. Runs contract_smoke_test.py + auth_smoke_test.py. No GCP/AWS credentials needed for
  contract tests (pure Python schema validation). Auth config tests use CLOUD_PROVIDER=local mode (validates
  .env.example completeness only). Separate job with CLOUD_PROVIDER=gcp uses GOOGLE_APPLICATION_CREDENTIALS secret."
  status: pending
- id: e2e-smoke-cloudbuild-step content: "Add contract smoke test as a cloudbuild step in
  unified-trading-deployment-v3/cloudbuild.yaml: runs BEFORE image push. Step: python -m pytest
  tests/smoke/test_contract_smoke.py tests/smoke/test_auth_smoke.py --cloud-provider=${\_CLOUD_PROVIDER:-gcp}. Cloud
  agnostic: \_CLOUD_PROVIDER substitution variable; same step works for GCP and AWS CodeBuild with different var
  injection." status: pending
- id: e2e-service-pair-registry content: | Create unified-trading-deployment-v3/configs/service-pairs.yaml: SSOT for all
  service-to-service data flows. Each entry: producer, consumer, topic/endpoint, batch_schema_class, live_schema_class,
  auth_method (oauth/mtls/internal_sa). Used by contract_smoke_test.py and auth_smoke_test.py to enumerate what to
  check. This replaces scattered knowledge of who talks to whom. status: pending
- id: aws-compute-stubs-wire content: "AWS compute stubs in UTD V3 backends/ are READY (aws_batch.py, aws_ec2.py) but
  not fully wired. Cloud-agnostic-migration.md says Layer 4 = GCP implemented, AWS stubs ready. Verify: (1)
  provider_factory.py returns correct AWS backend when CLOUD_PROVIDER=aws; (2) aws_batch.py and aws_ec2.py match the
  interface of cloud_run.py (same submit/status/cancel methods); (3) test_cloud_agnostic_paths.py covers AWS paths with
  mocks; (4) all checklist.\*.yaml have aws_equivalent fields." status: pending
- id: aws-secret-naming-parity content: "AWS Secrets Manager naming must mirror GCP Secret Manager canonical names.
  Enforce: exec-{client}-{venue}-{type} works on both (GCP SM uses same name, AWS SM uses same name in target region).
  Update auth-secret-manager-naming todo to cover AWS. Add CLOUD_PROVIDER branch to auth_smoke_test.py." status: pending
- id: aws-cloudbuild-parity content: "Verify all GCP cloudbuild.yaml have equivalent AWS CodeBuild buildspec.aws.yaml
  (execution-service already has buildspec.aws.yaml). Audit: which repos have cloudbuild.yaml but no buildspec.aws.yaml.
  Add missing buildspec files using same Docker pattern as GCP." status: pending
- id: aws-migration-cursor-rule content: "No cursor rule for cloud-agnostic coding. Create
  .cursor/rules/cloud-agnostic.mdc: RULE: All cloud I/O goes through get_storage_client(), get_secret_client(),
  GCSEventSink — never direct google-cloud-\* or boto3. CLOUD_PROVIDER env var switches provider. Test both paths in
  test_cloud_agnostic_paths.py. GCP primary; AWS secondary. Migration guide:
  05-infrastructure/cloud-agnostic-migration.md." status: pending
- id: ssot-checklist-auth-alignment content: | UTD V3 has 19 configs/checklist.\*.yaml per service (deployment
  readiness). Codex has 07-security/service-to-service-auth.md (mTLS spec, Specification Phase). These are NOT aligned:
  checklists have no auth_setup section; auth doc has no per-service checklist. SSOT work: (1) Add auth_setup block to
  checklist.template.yaml: local_auth_method, github_secret_name, cloudbuild_sa_roles, inter_service_auth
  (none/oauth/mtls), aws_secret_name; (2) Backfill all 19 checklists with auth_setup block; (3) Update
  07-security/service-to-service-auth.md: add per-service matrix (which services talk to which, current auth method vs
  target mTLS); (4) auth_smoke_test.py reads checklists as its expected config — checklist IS the spec. status: pending
- id: ssot-runtime-topology-manifest content: | Formalize deployment runtime topology SSOT in
  unified-trading-deployment-v3/configs/runtime-topology.yaml and make deployment tooling consume it. Scope: (1) define
  transport by mode (batch/live) and deployment profile (distributed/co_located_vm), (2) encode hybrid live in-memory
  allowance for MDPS<-MTDH only under co_located_vm, (3) wire dependency checks to skip GCS when dependency_check=none,
  (4) update codex TOPOLOGY-DAG.md + configs/README.md + cursor rule to reference runtime-topology.yaml as
  authoritative. COMPLETED: runtime-topology.yaml created at unified-trading-deployment-v3/configs/runtime-topology.yaml
  status: completed
- id: ssot-success-criteria-update content: | All checklist.\*.yaml success_criteria sections must be updated for new
  architectural goals: (1) UI is separate repo — not co-located (new arch-ui-separation-rule); (2) Service has no direct
  cloud SDK imports — all via UCLI/UTS; (3) CLOUD_PROVIDER=aws passes all tests (cloud agnostic); (4) Contract smoke
  test passes for all producer/consumer pairs; (5) Auth config smoke test passes for local + github + cloudbuild; (6)
  quality-gates.sh passes with no suppressions in ARCHITECTURAL_VIOLATION category. Use 4 parallel agents (5 checklists
  each) to backfill. status: pending
- id: ssot-service-to-service-auth-implement content: | 07-security/service-to-service-auth.md is Specification Phase —
  mTLS not implemented. For the short term (pre-mTLS), standardise on Google OAuth service accounts for inter-service
  calls (each service has a SA, callers use SA token). Implement: (1) add INTERNAL_SERVICE_AUTH_TOKEN env var to all
  services; (2) FastAPI dependency check_internal_auth() in execution-results-api, health-monitor-api; (3)
  auth_smoke_test.py validates token env var present in every service config; (4) Update codex
  service-to-service-auth.md: add Phase 0 (SA OAuth) before Phase 1 (mTLS). status: pending isProject: true

---

# Consolidated Remaining Work

> Supersedes 12 archived plans. All pending todos across the system, deduplicated and organized. Archived originals:
> `.cursor/plans/archive/`

---

## Execution Order

> **This plan has been split into 3 phase files. Execute phases in strict order.** See
> `unified-trading-pm/plans/cursor-plans/` for the authoritative phase plans.

### Phase Index (execute in order — do NOT start phase N until phase N-1 is fully done)

| Phase       | File                                      | Scope                                                                                                                                              | Done When                                                                                                                           |
| ----------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Phase 1** | `phase1_foundation_prep.md`               | Naming cleanup, SSOT docs, CI/CD rollout to 55 repos, deployment structure split (UTD V3 → 4 repos), QG baseline audit                             | All 55 repos have quickmerge + commit-msg hook; CI/CD pipeline live; deployment-service/api/ui/system-integration-tests repos exist |
| **Phase 2** | `phase2_library_tier_hardening.md`        | Global violation sweep, T0→T1→T2→T3 with Step A→B→C→D1→D5 per tier                                                                                 | All T0–T3 repos pass full quickmerge (D5) with act simulation                                                                       |
| **Phase 3** | `phase3_service_hardening_integration.md` | T4 services (DAG pipeline order), T5 API services, T6 UIs, integration layers (L1–L3), post-refactor sandbox deploy + L2+L3a+L3b + declare healthy | All tiers green; L3b (full e2e) passes; versions bump to 1.0.0                                                                      |

> **Canonical DAG (SSOT):** workspace-manifest.json → arch_tier field per repo. T0 = AC, UIC_INT, UCI, UEI, UCLI, URDI,
> EAL, MEL T1 = UTS T2 = UMI, UTEI, UDEI, USEI, UML, UFC, UPI T3 = UDC T4 = Services (14): IS, MTDH, MDPS, FCS, FDS,
> FVS, FOS, MLTR, MLIN, STR, EXEC, PBS, PNL, RES, AS (note: MTDH = market-tick-data-service) T5 = API Services: ERA,
> MDA, CRA (execution-results-api, market-data-api, client-reporting-api) T6 = UIs (11)
>
> **INVARIANT: Never touch tier N until tier N-1 is fully green (quickmerge passing).** **INVARIANT: Within each tier,
> follow the meta-flow below — no shortcuts.** **INVARIANT: No quickmerge until Phase 1 CI/CD rollout (STREAM A) is
> complete.**

### Meta-Flow (apply at every tier level, in order)

```
PRECONDITION — PHASE 0 MUST BE FULLY COMPLETE FIRST:
  - quickmerge.sh template synced to ALL 53 repos (agents get stuck otherwise)
  - commit-msg hook installed in ALL 53 repos
  - GitHub Actions dep-branch clone mechanic live
  - Cloud Build feature branch trigger live
  - All versions in workspace-manifest.json reset to 0.x.x
  - DAG validated and locked (dag-enforcement.mdc cursor rule in place)

For each tier (T0 → T1 → T2 → T3 → T4 → T5 → T6):

  STEP 0 — PRE-FLIGHT (run in every repo before touching any code)
    Fix ALL blocking QG violations present in the repo. Quickmerge WILL fail if skipped.
    Scan and fix before first commit:
      - os.getenv("KEY", "") or os.getenv("KEY")  → config class or os.environ["KEY"]
      - bare except:                               → specific exception type
      - except Exception: pass                     → log + reraise or @handle_api_errors
      - except ImportError: ...fallback...         → fail loud, no fallback imports
      - os.getenv("KEY", "") / config.x or ""      → Pydantic required or raise ValueError
      - File >900 lines                            → split by SRP
      - Function >100 / method >50 lines           → extract helpers
      - Any type annotations                       → TypedDict/Protocol/specific type
      - List[x], Dict[x,y], Tuple[x]              → list[x], dict[x,y], tuple[x]
      - datetime.now() / datetime.utcnow()         → datetime.now(timezone.utc)
      - print() in source                          → logger.info()

  STEP A — DEPLOY STRUCTURE
    Fix cloudbuild.yaml, quality-gates.sh, workspace-manifest.json, pyproject.toml
    for every repo at this tier. CI must be able to run before any code changes.

  STEP B — TESTS FIRST
    Write/fix unit tests. Import smoke test must pass (python -c "import pkg" exits 0).
    Contract tests where applicable. Tests are written BEFORE code rewrites.

  STEP C — CODE REWRITE
    Fix tier violations, type errors, import paths, QG violations.
    Use dep-branch cascade so multi-repo changes stay in sync.

  STEP D — PROGRESSIVE VALIDATION (run in order, fix issues between each)

    D1. quickmerge --lint-only
        Lint + format only. Fastest feedback. Catches: syntax, import ordering, formatting.

    D2. quickmerge --unit-only
        Lint + type check + unit tests only (no integration, no act).
        Catches: import errors, type errors, unit test regressions.

    D3. quickmerge --qg-only
        Full quality gates (lint + type + all tests + codex checks) but NO git ops (no commit, no PR).
        Equivalent to running quality-gates.sh but through quickmerge so dep validation still runs.
        Catches: integration test failures, coverage gaps, codex violations.

    D4. quickmerge --quick
        Full quality gates + git ops, but SKIP act simulation.
        Catches: everything except GitHub Actions compatibility.

    D5. quickmerge (full — no flags)
        Full validation including act simulation.
        Tier is "green" ONLY when this passes. Do NOT move to next tier until green.
```

Max parallel sub-agents: **10**. Annotations show parallelism at each step.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 0 — CI/CD + DEPLOYMENT INFRASTRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MUST complete entirely before tier work starts. Runs in 3 parallel streams.

  STREAM A — CI/CD WORKFLOW (gates ALL multi-repo work — must finish before any tier work)
  ⛔ WITHOUT THIS: quickmerge never passes, agents loop forever. Run this FIRST in parallel.

  ✅ DONE: conventional-commits.mdc, always-use-quickmerge.mdc,
           never-revert-local-changes.mdc, path-dependency-ci.mdc,
           library-versioning.mdc, quickmerge template (cascade + --no-pr + --unit-only),
           codex feature-branch-workflow.md,
           workspace-manifest.json versions reset to 0.x.x (2026-02-28)

  STEP A0 — DAG VALIDATION [BLOCKING — precondition for entire plan]:
    Verify workspace-manifest.json arch_tier fields match canonical DAG.
    Verify no tier violations in pyproject.toml dependencies.
    DAG cursor rule (.cursor/rules/dag-enforcement.mdc) must be in place.
    If DAG has issues: fix them NOW, before any other work starts.
    Todos from DAG plan:
      dag-ssot-align — reconcile manifest + topology docs
      dag-tier-corrections — fix tier numbering mismatches
      dag-orphan-repos-manifest — add 4 missing API service repos
      dag-mel-tier-mismatch — fix MEL visual bug in SVG

  STEP A1 — QUICKMERGE + VERSION-BUMP PROPAGATION [BLOCKING — do before anything else] [10 agents PARALLEL]:
    Push updated quickmerge.sh template AND version-bump.yml to ALL 53 repos simultaneously.
    Each agent handles 5-6 repos:
      1. Copy quickmerge template → scripts/quickmerge.sh
      2. Copy version-bump.yml → .github/workflows/version-bump.yml
         (auto-triggered on push to main, reads conventional commit prefix, pre-1.0.0 safety)
      3. Verify pyproject.toml exists with version field (create minimal one if missing)
      4. git commit "chore: sync quickmerge template + version-bump workflow" → git push
    ⛔ Nothing else starts until all 53 repos have both templates.
    Version-bump.yml SSOT: unified-trading-pm/.github/workflows/version-bump.yml (for services/libraries)
    Note: PM version-bump also updates workspace-manifest.json; other repos bump their own pyproject.toml only.

  STEP A2 — COMMIT-MSG HOOKS [4 agents PARALLEL, after A1]:
    ci-conventional-commits-cursor-rule  — add commit-msg hook to all 53 repos
                                           (validates feat:/fix:/chore:/BREAKING CHANGE: prefix)
    ci-ar-local-version-verification     — verify GCP AR accepts PEP 440 local (+) versions
    ci-refactor-scope-manifest           — add refactor_scope field to workspace-manifest.json
    ci-versions-reset-pyproject          — verify all pyproject.toml versions match 0.x.x manifest
                                           (update any that are >=1.0.0 to match manifest)

  STEP A3 — CI/CD PIPELINE [3 agents PARALLEL, after A2]:
    ci-github-actions-dep-branch-clone   — ${DEP_BRANCH:-main} + git ls-remote fallback in all quality-gates.yml
    ci-cloud-build-feature-branch-trigger + ci-cloud-build-feature-version-inject
    ci-auto-version-bump-github-action   — GH Action bumps version on main merge from commit prefix
  ── then [1 agent, after Stream B]: ci-temp-manifest-schema

  STREAM B — DEPLOYMENT STRUCTURE (UTD V3 four-way split + system-integration-tests)
    [4 agents PARALLEL]
    arch-exec-services-visualizer-extract  — extract visualizer-ui + visualizer-api from exec-services
    arch-deployment-v3-ui-extract + deployment-v3-four-way-split
                                           — split UTD V3 → deployment-service + deployment-api + deployment-ui
                                           (shared-config dissolved; configs in deployment-service)
    ui-service-separation-audit-full       — audit all remaining services for embedded UI
    integration-system-integration-tests-repo — create system-integration-tests repo per new-repo-setup.md
  ── then [2 agents PARALLEL]:
    integration-layer2-infra-verify       — add verify_infra.py to deployment-service; gate deployment success
    integration-layer3-implement          — implement Layer 3a + 3b in system-integration-tests (sequential)
  ── then [1 agent]:
    hybrid-live-seam — implement/document hybrid live in-memory adapter seam for MDPS
    ssot-runtime-topology-manifest — ✅ DONE: runtime-topology.yaml created + configs README updated
  ── then: ci-temp-manifest-schema (needs deployment-api from above)

  STREAM C — QG BASELINE AUDIT (can run concurrently with A and B)
    aws-migration-cursor-rule              — cloud-agnostic.mdc
    ci-manifest-status-fields             — add ci_status/qg_status fields to workspace-manifest
    [10 agents] Add quality-gates.sh to 12 repos missing it
    [10 agents] Run QG baseline on all 30 repos → record in manifest  (after QG files added)
    [5 agents]  Verify cloudbuild.yaml invokes QG inside Docker image (6 repos each)
    aws-compute-stubs-wire + aws-secret-naming-parity + aws-cloudbuild-parity [3 agents PARALLEL]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GLOBAL VIOLATION SWEEP (after Phase 0, before Tier work)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mechanical find-and-replace violations that block quickmerge everywhere.
Run ONCE across all repos. Per-tier Step 0 handles complex violations
(file splitting, Any-type replacement) that require code understanding.

  [10 agents PARALLEL, 5-6 repos each]:
    Scan ALL repos for:
      os.getenv("KEY", "")          → config class field or os.environ["KEY"]
      os.getenv("KEY")              → config class field or os.environ["KEY"]
      bare except:                  → specific exception type
      except Exception: pass        → log + reraise
      print() in source             → logger.info()
      datetime.now()                → datetime.now(timezone.utc)
      datetime.utcnow()            → datetime.now(timezone.utc)
      List[x], Dict[x,y], Tuple[x] → list[x], dict[x,y], tuple[x]
    Commit: "fix: global violation sweep — mechanical QG fixes"
    Do NOT attempt: file splitting, Any-type fixes, function extraction (those are per-tier Step 0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 0 — AC, UIC_INT, UCI, UEI, UCLI, URDI, EAL, MEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRES: Phase 0 complete.
INVARIANT: All T0 repos must be fully green before any T1 work starts.

  T0 has no inter-library deps (pure compute / foundational). All 8 repos work in PARALLEL.

  STEP A — DEPLOY STRUCTURE [8 agents PARALLEL, 1 per repo]:
    Each agent: verify cloudbuild.yaml, quality-gates.sh, pyproject.toml, workspace-manifest.json
    Todos: ci-quality-gates-missing-repos (AC, UEI, URDI), ci-cloudbuild-quality-gate-wire,
           ci-bypass-audit-missing-repos, ci-quality-gates-alignment

  STEP B — TESTS FIRST [8 agents PARALLEL]:
    Each agent: import smoke test (python -c "import pkg" exits 0); fix/write unit tests
    LAYER 0 (contract alignment) — MUST complete in T0:
      integration-layer0-ac-uic-unit     — unified-api-contracts: test_contract_alignment.py (internal consistency)
      integration-layer0-ac-uic-integration — unified-api-contracts: test_ac_uic_alignment.py (AC→UIC schema pairs)
      integration-layer0-uic-ac-unit     — unified-internal-contracts: test_contract_alignment.py (internal)
      integration-layer0-uic-ac-integration — unified-internal-contracts: test_uic_ac_alignment.py (UIC→AC)
      (Both directions: AC↔UIC. SSOT: 06-coding-standards/integration-testing-layers.md)
    Todos: ic-uic-coverage-floor (UIC_INT 35%→80%), ic-uic-py-typed, ac-coverage-90
           ac-ccxt-completeness, ac-fee-borrow-all-venues, ac-risk-infrastructure,
           ac-funding-settlement-portfolio-margin, ac-vol-surface-all-venues,
           ac-sentiment-oi-all-venues, ac-account-lifecycle-all-venues,
           ac-aggregate-trades-fills-mark-price, ac-shared-schema-extensions,
           ac-restructure, ac-dual-structure-doc
           ic-greeks-position-schema, ic-pnl-breakdown-schema, ic-circuit-breaker-schema,
           ic-eod-settlement-contract, ic-feature-contracts, ic-ml-training-contracts,
           ic-rebalance-instruction, ic-portfolio-risk-contracts, ic-client-account-domain-model
           ic-unified-internal-repo (create repo)

  STEP C — CODE REWRITE [8 agents PARALLEL]:
    Each agent: fix tier violations, imports, type errors, quality gate violations
    Todos: lib-phase3-urdi-setup (URDI T0 hardening; get_secret_client via UCLI),
           mel-deps-remove (MEL zero inter-lib deps), dag-mel-tier-mismatch,
           cohesion-uic-int-unified-api-contracts-dep, auth-endpoint-registry-unvalidated,
           vcr-urdi-parse-raw-umi-stubs, vcr-public-venues (cassettes in AC),
           ac-exhaustive-schema-universe, quality-importerror-fallbacks (AC only),
           quality-large-file-splits (aws_schemas.py, venue_manifest.py, binance/schemas.py)

  STEP D — quickmerge --unit-only [8 agents PARALLEL, 1 per repo]
  STEP E — quickmerge full [8 agents PARALLEL] → T0 green gate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 1 — UTS (unified-trading-services)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRES: All T0 repos green.
Single repo — sequential sub-phases.

  STEP A — DEPLOY STRUCTURE:
    lib-phase5-t1-quality-gates (verify QG passes); ci-cloudbuild-quality-gate-wire for UTS

  STEP B — TESTS FIRST:
    qg-uts-conftest-skip-pattern (fix GCP auth skip pattern);
    ConfigReloader test already in UTS (moved from UCI ✅)

  STEP C — CODE REWRITE:
    lib-phase1-uts-domain-cleanup (remove create_instruments_client etc. from __init__.py);
    lib-phase2-uts-rename-step1 (add unified_trading_services/ re-export package);
    dag-uts-v22-feature-audit (verify GCSEventSink, PubSubEventSink, QueueEventSink, ServiceCLI,
    BatchOrchestrator, @with_retry, setup_service, StateStore, BaseCloudWriter, GracefulShutdownHandler
    are all implemented); quality-importerror-fallbacks (UTS only);
    uts-v5-cleanup (clean optional extras to remove tier leakage and stale package names)

  STEP D — quickmerge --unit-only
  STEP E — quickmerge full → T1 green gate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 2 — UMI, UTEI, UDEI, USEI, UML, UFC, UPI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRES: T0 + T1 green.
All 7 repos independent of each other at T2 — work in PARALLEL.

  STEP A — DEPLOY STRUCTURE [7 agents PARALLEL]:
    lib-phase5-t2-quality-gates (UDC+UMI, UTEI+UML, UFC+UPI+URDI QG checklist);
    ci-quality-gates-missing-repos (UTEI, UPI); cohesion-umi-udc-dep-violation (remove UDC from UMI)

  STEP B — TESTS FIRST [7 agents PARALLEL]:
    vcr-public-venues (UMI VCR cassettes: kalshi, polymarket, thegraph etc.);
    vcr-new-adapters-public (UMI); vcr-new-adapters-cefi-sports; vcr-new-adapters-tradfi-altdata;
    vcr-enhanced-error-high-priority (instruments-service 62 — test fixes);
    p0-umi-skipped-test (unskip after p0-canonical-swap-fix); usei-v1-betfair-pinnacle

  STEP C — CODE REWRITE [7 agents PARALLEL]:
    p0-canonical-swap-fix (UIC CanonicalSwap stale installed — bump + reinstall);
    vcr-urdi-parse-raw-umi-stubs (UMI stubs); lib-phase2-udc-rename-step1;
    vcr-new-adapters-cefi-sports; vcr-new-adapters-tradfi-altdata;
    cohesion-upi-pbm-dependency (UPI adapters feed PBM); quality-importerror-fallbacks (T2 only);
    uml-protocol-refactor (define ModelArtifactStore protocol in UML, remove direct UDC imports)

  STEP D — quickmerge --unit-only [7 agents PARALLEL]
  STEP E — quickmerge full [7 agents PARALLEL] → T2 green gate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 3 — UDC (unified-domain-client)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRES: T0 + T1 + T2 green.
Single repo — sequential sub-phases.

  STEP A — DEPLOY STRUCTURE:
    lib-phase1-udc-tier2-compliance (replace CloudTarget/get_config from UCS with UCLI equivalents;
    remove UTS dep from pyproject.toml; add UCLI); lib-phase2-udc-rename-step1

  STEP B — TESTS FIRST:
    ic-deprecated-withdraw-cleanup; ic-trad-fi-datasource-tag; ic-onchain-freshness-contract

  STEP C — CODE REWRITE:
    lib-phase3-instruments-service-urdi-wire (UDC → URDI wiring — done here as UDC consumer);
    lib-phase2-rename-step2 (update all consumers after rename);
    udc-artifact-impl (implement GcsModelArtifactStore in UDC, wire in ML services)

  STEP D — quickmerge --unit-only
  STEP E — quickmerge full → T3 green gate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 4 — SERVICES (14 repos, in DAG pipeline order)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRES: T0+T1+T2+T3 green. NEVER change service code without its library tier being green.
DAG pipeline order (data flow): IS → MTDH → MDPS → FCS/FDS/FVS/FOS → MLTR → MLIN → STR → EXEC
                                 IS also feeds: PBS → PNL → RES → AS (monitoring pipeline)

  Batch A — INSTRUMENTS-SERVICE (IS) [gates all other services]:
    STEP A: lib-phase4-connectivity-audit (IS as pilot); lib-phase7-instruments-service-validation
    STEP B: Tests: verify IS import smoke test; VCR cassettes via URDI
    STEP C: lib-phase6-service-code-adjustment (IS); exec-svc-cross-svc-deps (fix IS service→service dep)
            qg-upload-events-legacy (IS cloud_instrument_storage.py)
    STEP D: quickmerge --unit-only
    STEP E: quickmerge full

  Batch B — DATA PIPELINE (MTDH, MDPS) [2 agents PARALLEL, after IS green]:
    STEP A: Deploy structure both repos
    STEP B: Tests first (unit tests; batch/live seam tests)
    STEP C: p0-strategy-live-mode (live seams); qg-upload-events-legacy (MDPS);
            lib-phase6-service-code-adjustment; exec-svc-cross-svc-deps (remove market-tick-data-handler dep)
    STEP D/E: quickmerge --unit-only then full [2 agents PARALLEL]

  Batch C — FEATURES LAYER (FCS, FDS, FVS, FOS) [4 agents PARALLEL, after MTDH+MDPS green]:
    STEP A: Deploy structure all 4 repos
    STEP B: Tests first; ic-feature-contracts (UIC_INT feature schemas)
    STEP C: vcr-enhanced-error-remaining (FDS, FVS, FOS); features-sports-service-full;
            lib-phase6-service-code-adjustment (features); qg-fds-uncommitted-changes
    STEP D/E: quickmerge --unit-only then full [4 agents PARALLEL]

  Batch D — ML PIPELINE (MLTR, MLIN) [2 agents PARALLEL, after features green]:
    STEP A: Deploy structure
    STEP B: Tests; ic-ml-training-contracts; ic-portfolio-risk-contracts
    STEP C: p0-ml-bare-except; lib-phase6-service-code-adjustment (ML);
            qg-backtest-engine-reportany; ui-ml-training-config-wire
    STEP D/E: quickmerge --unit-only then full [2 agents PARALLEL]

  Batch E — STRATEGY + EXECUTION (STR, EXEC) [2 agents PARALLEL, after ML green]:
    STEP A: Deploy structure
    STEP B: Tests; ic-strategy-domain-event-validation; p0-cdc-tests (contract tests)
    STEP C: p0-strategy-live-mode (live mode seams); lib-phase6-service-code-adjustment;
            qg-strategy-service-gitignore; qg-strategy-service-print-pdf;
            qg-strategy-service-tier2-dep; qg-strategy-domain-adapter-type;
            qg-exec-import-error-remaining; qg-exec-services-codex-18;
            qg-pip-audit-exec-services; qg-exec-services-smoke-import;
            qg-central-element-test-code; vcr-enhanced-error-high-priority (exec-services 201);
            quality-importerror-fallbacks (exec-services); quality-large-file-splits (engine.py);
            quality-type-ignore-arch-violations; ci-arch-violations-fix
    STEP D/E: quickmerge --unit-only then full [2 agents PARALLEL]

  Batch F — MONITORING PIPELINE (PBS, PNL, RES, AS) [4 agents PARALLEL, after EXEC green]:
    STEP A: Deploy structure
    STEP B: Tests; ic-pnl-breakdown-schema; ic-greeks-position-schema; ic-circuit-breaker-schema;
            ic-eod-settlement-contract; ic-risk-service-complete
    STEP C: ic-pnl-attribution-complete; ic-risk-service-complete; obs-metrics-aggregator-api;
            lib-phase6-service-code-adjustment (monitoring); qg-asyncio-run-audit
    STEP D/E: quickmerge --unit-only then full [4 agents PARALLEL]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 5 — API SERVICES (ERA, MDA, CRS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRES: All T4 services green.
3 repos independent of each other — PARALLEL.

  STEP A: dag-orphan-repos-manifest (ensure all 3 in manifest with correct type/tier);
          dag-api-services-cluster (confirm standalone repos, FastAPI only, no engine code)
  STEP B: Tests; p0-cdc-tests (consumer tests for ERA/MDA/CRS)
  STEP C: p0-exec-results-api-types (replace dict[str,Any] with TypedDict/Pydantic);
          vcr-execution-results-api-uic; p0-ui-sse (SSE endpoints on ERA + health-monitor-api);
          ssot-service-to-service-auth-implement; auth-credentials-registry
  STEP D/E: quickmerge --unit-only then full [3 agents PARALLEL]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIER 6 — UIs (11 repos)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRES: T5 API Services green.
All UIs independent of each other — PARALLEL.

  STEP A: ui-local-dev-setup (.env.local.example for all 11 UIs)
  STEP B: Tests; ui-smoke-tests-and-deslop; ui-runtime-validation
  STEP C [11 agents PARALLEL]:
    Agent 1:  auth-trading-analytics-ui (OAuth TRADER + /positions /pnl /executions /risk)
    Agent 2:  ui-orderbook-viz + ui-latency-plots
    Agent 3:  ui-system-health-page
    Agent 4:  auth-onboarding-ui-gaps + auth-onboarding-ui-complete
    Agent 5:  auth-manual-trading-consolidate (live-health-monitor-ui)
    Agent 6:  auth-config-promotion-workflow (BacktestGridResult → StrategyConfig)
    Agent 7:  auth-ml-training-ui
    Agent 8:  auth-ai-report-summaries
    Agent 9:  deployment-ui-implement (full implementation after T5 split)
    Agent 10: obs-grafana-export + obs-prometheus-codex
    Agent 11: ui-skeleton-assess (execution-analytics-ui, client-reporting-ui, settlement-ui)
  STEP D/E: quickmerge --unit-only then full [batched in groups of 4]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CROSS-CUTTING (run throughout, not tier-gated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Auth + credentials (starts at Phase 0 STREAM B, completes across tiers as services green):
    auth-credentials-registry, auth-secret-manager-naming, auth-setup-secret-script,
    auth-three-tranche-data-wiring, ssot-checklist-auth-alignment, ssot-success-criteria-update,
    auth-ibkr-corp-actions, auth-sports-migration-batch1/batch2

  Codex + SSOT docs (update as each tier completes):
    codex-tier-arch-conflict-resolve, codex-service-dependency-diagram-v3,
    codex-ui-service-separation-doc, codex-orphan-repos-doc, codex-service-pair-flows-doc,
    codex-quality-gates-aws-parity, codex-s2s-auth-phase0-impl

  Final QG sweep (after all tiers green):
    p0-reportany-error-all-repos [10 agents], vcr-quality-gates,
    ci-per-repo-status-run, ci-arch-violations-fix (any remaining)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTEGRATION TESTING LAYERS (cumulative, in dependency order)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SSOT: unified-trading-/codex/06-coding-standards/integration-testing-layers.md
Cursor rule: .cursor/rules/integration-testing-layers.mdc

  LAYER 0 — CONTRACT ALIGNMENT (runs at T0, in quickmerge)
    Location: unified-api-contracts + unified-internal-contracts tests/
    Tests AC↔UIC schema pairs for structural compatibility (field names, types, required/optional)
    Both directions: AC validates against UIC; UIC validates against AC.
    Todos (part of T0 STEP B):
      integration-layer0-ac-uic-unit         — unified-api-contracts: test_contract_alignment.py (internal)
      integration-layer0-ac-uic-integration  — unified-api-contracts: test_ac_uic_alignment.py (AC→UIC pairs)
      integration-layer0-uic-ac-unit         — unified-internal-contracts: test_contract_alignment.py
      integration-layer0-uic-ac-integration  — unified-internal-contracts: test_uic_ac_alignment.py

  LAYER 1 — SCHEMA ROBUSTNESS (runs per-service at each tier, in quickmerge)
    Location: each repo tests/unit/test_schema_robustness.py
    Tests: required field missing → ValidationError; optional absent → passes; wrong type → fails
    Written as part of STEP B at each tier for every repo that defines or consumes Pydantic schemas.
    No new todos — folded into existing STEP B per-tier work.

  LAYER 2 — INFRASTRUCTURE VERIFICATION (runs post-deploy, NOT in quickmerge)
    Location: deployment-service/scripts/verify_infra.py → exposed as GET /infra/health in deployment-api
    Tests: GCS buckets exist + IAM, PubSub topics exist + subscriptions, Secret Manager entries exist
    REQUIRES: deployment-service extracted from UTD V3 (Phase 0 Stream B)
    Todos:
      integration-layer2-infra-verify — implement verify_infra.py in deployment-service

  LAYER 3 — PIPELINE SMOKE + E2E (runs post-deploy, after Layer 2 passes)
    Location: system-integration-tests/ (standalone repo, arch_tier: integration)
    Layer 3a (smoke): @pytest.mark.smoke — happy path, <5 min, pre-deploy confidence gate
    Layer 3b (full):  @pytest.mark.full_e2e — corner cases, auth, perf, 15-30 min
    Sequential: 3a must pass before 3b starts. If 3a fails, 3b is skipped.
    REQUIRES: system-integration-tests repo created (Phase 0 Stream B)
    Zero Python imports from services — HTTP/GCS/PubSub interaction only.
    Todos:
      integration-system-integration-tests-repo — create repo per new-repo-setup.md
      integration-layer3-implement — implement Layer 3a + 3b (sequential smoke → full)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST-REFACTOR VALIDATION (final phase, after ALL tiers green)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIRES: All tiers (T0–T6) fully green. Deployment split complete.

This is the first time the full system is validated end-to-end under the new architecture.
Sequence (strictly ordered):

  1. DEPLOYMENT REFACTOR [Phase 0 Stream B, already scheduled]:
     UTD V3 → deployment-service + deployment-api + deployment-ui
     system-integration-tests repo created and scaffolded
     (The deployment refactor itself is NOT tested until this phase — it is built during
     Phase 0 Stream B but cannot be validated until all tiers are green.)

  2. DEPLOY TO SANDBOX:
     Use deployment-service CLI to deploy all T4 services to GCP sandbox project.
     deployment-api must start cleanly on Cloud Run.

  3. LAYER 2 — INFRASTRUCTURE VERIFY:
     GET /infra/health → all checks pass (buckets, topics, IAM, secrets)
     If Layer 2 fails: fix infrastructure before proceeding. DO NOT skip.

  4. LAYER 3a — PIPELINE SMOKE:
     system-integration-tests: pytest -m smoke
     Happy path: one date, one venue, one instrument through full pipeline.
     If 3a fails: debug wire mismatches, fix, re-run. Do NOT proceed to 3b.

  5. LAYER 3b — FULL E2E:
     system-integration-tests: pytest -m full_e2e
     Corner cases, auth flows, multi-date, performance baseline.
     If 3b fails: investigate, fix, re-run.

  6. SYSTEM DECLARED HEALTHY:
     All 4 layers pass. deployment-api marks deployment status as "healthy."
     Merge staging → main. GitHub Action bumps versions to 1.0.0 (first stable).

  Todos (new):
    postrefactor-sandbox-deploy       — deploy all services to sandbox via deployment-service
    postrefactor-layer2-run           — run GET /infra/health, resolve failures
    postrefactor-layer3a-run          — run pytest -m smoke in system-integration-tests
    postrefactor-layer3b-run          — run pytest -m full_e2e in system-integration-tests
    postrefactor-declare-healthy      — mark all repos healthy, merge staging → main
```

---

# ─── SECTION O: CODEX + DEPLOYMENT-V3 AUDIT FINDINGS (2026-02-28) ────────────

# Audit of unified-trading-codex + unified-trading-deployment-v3/configs + /docs

- id: codex-tier-arch-conflict-resolve content: > CONFLICT: 04-architecture/TIER-ARCHITECTURE.md (5-tier) vs
  05-infrastructure/unified-libraries/TIER-ARCHITECTURE.md (3-tier model scoped to libraries only). The 5-tier model in
  04-architecture is canonical per DAG. The 3-tier in 05-infra is intentionally scoped to library tiers (T0/T1/T2) —
  this is VALID if clearly stated. Fix: add a header to 05-infrastructure/unified-libraries/TIER-ARCHITECTURE.md
  clarifying it covers library-layer tiers (T0-T2 only) and defers to 04-architecture for full system tier model. Also
  update 05-infra doc to add missing libs (EAL, UIC_INT, MEL, UDEI, USEI). status: pending priority: P1
- id: codex-service-dependency-diagram-v3 content: > 04-architecture/SERVICE_DEPENDENCY_DIAGRAM.md and
  SERVICE_DEPENDENCY_GRAPH.md both reference deployment-v2. Update both to reference deployment-v3 and add the 4 orphan
  API service repos (execution-results-api, market-data-api, client-reporting-api, strategy-ui) as explicit nodes in the
  graph. status: pending priority: P1
- id: codex-ui-service-separation-doc content: > MISSING DOC: Add
  unified-trading-/codex/04-architecture/ui-service-separation.md (or 06-coding-standards/ui-service-separation.md)
  documenting: (1) UI repos must be separate git repos from service engine; (2) Services expose FastAPI + SSE; (3) UIs
  consume via HTTP/SSE only; (4) No direct library imports from service engine repos in UI. Mirror the
  .cursor/rules/ui-service-separation.mdc content but as a codex reference doc. status: pending priority: P1
- id: codex-orphan-repos-doc content: > MISSING DOC: Add 04-architecture/api-services-cluster.md covering the 4 API
  service repos that live between the service tier and UIs per the canonical DAG: execution-results-api (ERA),
  market-data-api (MDA), client-reporting-api (CRA), strategy-ui. For each: repo URL, status
  (deployed/in-progress/shell), FastAPI+OAuth middleware pattern, which service it proxies, which UI it serves. status:
  pending priority: P1
- id: codex-service-pair-flows-doc content: > MISSING DOC: Add 08-workflows/service-pair-flows.md documenting all data
  flows per the canonical DAG edges: MTDH→GCS (batch Parquet), MTDH→PubSub (live events),
  GCS→FCS/FDS/FVS/FOS/MLTR/MLIN/STR/EXEC (batch read), PubSub→FDS/FVS/STR/MLIN (live), EXEC→ERA (batch write),
  IS→UMI/UDC (instrument resolution). Format: YAML service-pairs.yaml with batch_schema_class, live_schema_class,
  message_bus, producer, consumers per edge. This becomes the SSOT for e2e-service-pair-registry task. status: pending
  priority: P0
- id: codex-quality-gates-aws-parity content: > 06-coding-standards/quality-gates.md missing: (1) AWS CodeBuild parity
  section showing buildspec.aws.yaml equivalent to cloudbuild.yaml; (2) CLOUD_PROVIDER=aws test matrix. Add a "Cloud
  Provider Parity" table: each QG step mapped to GCP Cloud Build step AND AWS CodeBuild phase. Reference
  cloud-agnostic-migration.md. status: pending priority: P1
- id: codex-s2s-auth-phase0-impl content: > 07-security/service-to-service-auth.md now has Phase 0 (SA OAuth) section
  added (done). Next: implement Phase 0 in code — ssot-service-to-service-auth-implement already covers this but
  cross-link to this doc. Ensure auth_smoke_test.py validates SA token env var per service. Mark status: "Phase 0 in
  progress". status: pending priority: P0
- id: deploy-v3-docs-cleanup-done content: > COMPLETED (2026-02-28): Deleted 9 summary/status docs from
  deployment-v3/docs/ (ML_SESSION_COMPLETE, FINAL_STATUS_ALL_TOPICS, CLOUD_BUILD_IMPLEMENTATION_SUMMARY,
  COMPLETE_AUDIT_RESULTS, CSV_DUMP_AUDIT_FINAL, DOCUMENTATION_VALIDATION_MATRIX, AUDIT_TOPICS_1_2_3,
  AWS_MIGRATION_EXECUTION, abc.md). Archived 17 historical docs to docs/archive/. 32 active spec docs remain.
  Schema-change/ dir archived. status: completed

# ─── SECTION P: REPO STRUCTURE + DAG ALIGNMENT (2026-02-28) ─────────────────

- id: manifest-dag-corrections-done content: > COMPLETED (2026-02-28): workspace-manifest.json fully aligned with
  canonical DAG. (1) UDC arch_tier 2→3. (2) MEL arch_tier 2→0, deps cleared. (3) EAL+MEL moved to topological Level 0.
  (4) Tier 2 rule updated: now imports T0+T1 (not T0-only). (5) Tier 3 rule added for UDC. (6) api-services tier added
  for ERA/MDA/CRS. (7) UMI→UDC T2→T3 dep violation flagged in manifest known_violations. (8) completion_paths section
  added (CeFi, DeFi, Sports). status: completed
- id: orphan-repos-manifest-done content: > COMPLETED (2026-02-28): Added 4 orphan API service repos to
  workspace-manifest.json: execution-results-api (ERA), market-data-api (MDA), client-reporting-api (CRS), strategy-ui.
  All added with type=api-service|ui, arch_tier=api|ui, cluster=api-services, serves_ui, proxies_service fields. Added
  to topological Level 7. completion_path=cefi. status: completed
- id: sports-repos-scaffolded-done content: > COMPLETED (2026-02-28): Scaffolded features-sports-service and
  unified-sports-execution-interface in workspace. Each has pyproject.toml, **init**.py, README.md with completion path
  notes. USEI has BaseSportsAdapter Protocol stub. Both have status=scaffolded in manifest. NOT required for CeFi
  completion. status: completed
- id: mel-deps-remove content: > matching-engine-library must have zero inter-lib deps (Tier 0 pure compute). Current
  source may still import unified-trading-services or unified-config-interface. Audit matching-engine-library source: rg
  "from unified\_" matching-engine-library/ --type py. Remove any UTS/UCI imports — replace with stdlib typing only. Add
  to quality-gates.sh: tier-boundary check (no external lib imports). status: pending priority: P1
- id: features-sports-service-full content: > features-sports-service: Implement full sports feature pipeline using
  sports-betting-services repo as reference implementation. Extract: team form, H2H, referee, venue context, weather
  (Open Meteo), market odds signals. Wire to UFC FeatureCalculatorRegistry. Use UDC sports domain readers. Batch mode
  first (--mode batch GCS write), then live. Depends on: ac-exhaustive-schema-universe (sports schemas), USEI v0.1.0
  scaffolded (done). status: pending priority: P2 completion_path: sports
- id: usei-v1-betfair-pinnacle content: > unified-sports-execution-interface v1.0.0: Implement BetfairAdapter (CLOB via
  UTEI order logic — reuse SmartOrderRouter patterns) and PinnacleAdapter (fixed-odds REST API). Requires:
  unified-api-contracts Betfair + Pinnacle schemas + VCR cassettes. BaseSportsAdapter protocol exists (scaffolded).
  Betfair can reuse UTEI FillSchema/OrderSchema. status: pending priority: P2 completion_path: sports
  - id: execution-underscore-cleanup content: > COMPLETED (2026-02-28): execution_service/ (underscore) confirmed stale
    — no git, only contained empty utils/ subdir. Deleted. Zero orphan dirs remain. status: completed
  - id: infra-merge-utdv3 content: > ibkr-gateway-infra/ dir (workspace root) contains ibkr-gateway-infra/ibkr-gateway/
    Terraform config (main.tf, variables.tf). The DAG UTDV3 node explicitly lists "IBKR Gateway config" as part of
    unified-trading-deployment-v3. Fix: move ibkr-gateway-infra/ibkr-gateway/ →
    unified-trading-deployment-v3/infra/ibkr-gateway/ then delete ibkr-gateway-infra/. ibkr-gateway-infra/ added to
    manifest with known_violations flag pending this merge. status: pending priority: P1
  - id: dag-mel-tier-mismatch content: > DAG VISUAL BUG: canonical DAG SVG classifies MEL as tier2 (orange) with UTS→MEL
    and UCI→MEL edges. But MEL node text says "zero inter-lib deps" which is T0. Our codex and manifest correctly say
    T0. Next DAG redraw: move MEL to Tier 0 (blue), remove UTS→MEL and UCI→MEL edges. Code audit: mel-deps-remove task
    (rg "from unified\_" matching-engine-library/ to verify zero imports). status: pending priority: P1
  - id: deployment-ui-scaffold-done content: > COMPLETED (2026-02-28): Scaffolded deployment-ui/ per
    ui-service-separation rule. UTD-v3 DAG node mentions "Deploy UI" — separated into its own repo. Files: package.json
    (React 18, Vite 5, TS), src/main.tsx shell, README.md. Added to workspace-manifest.json (type: ui, merge_level: 9,
    status: scaffolded). [Note: UIs shifted from L8→L9 in tier-restructure 2026-02-28] status: completed
  - id: strategy-validation-scaffold-done content: > COMPLETED (2026-02-28): Scaffolded strategy-validation-service/
    (was in manifest as planned, no dir existed). Files: pyproject.toml, strategy_validation_service/**init**.py,
    README.md, tests/**init**.py. Status updated to scaffolded in manifest. CeFi post-commercialisation path. status:
    completed
  - id: dag-full-reconcile-done content: > COMPLETED (2026-02-28): Full DAG vs workspace vs manifest reconciliation.
    Repos added to manifest: unified-trading-pm (52 total now, was 49), deployment-ui, ibkr-gateway-infra,
    strategy-validation-service. Deleted: execution_service/ (stale underscore duplicate, no git, no unique content).
    Scaffolded: deployment-ui/, strategy-validation-service/. Orphans resolved: 0 workspace dirs missing from manifest
    (ibkr-gateway-infra tracked with known_violations). Remaining manual action: infra-merge-utdv3 (move Terraform from
    ibkr-gateway-infra into UTD-v3). status: completed
  - id: deployment-ui-implement content: > deployment-ui/ is scaffolded shell. Full implementation needed (depends on
    deployment-v3-four-way-split): (1) Orchestrator run status dashboard — SSE stream from deployment-api/deployments
    endpoint (2) Cloud Build trigger buttons (OAuth-gated) — POST /cloud-builds/trigger; button disabled for non-admin
    OAuth tokens (3) Shard calculator visualization — GET /capabilities (4) Cloud Run service health panel — GET
    /service-status with auto-refresh (5) IBKR Gateway config UI — connection status, heartbeat monitor (6)
    .env.local.example: VITE_API_URL=[http://localhost:8001](http://localhost:8001), VITE_OAUTH_CLIENT_ID=,
    VITE_ENV=local See: unified-trading-/codex/05-infrastructure/UI-DEPENDENCY-MATRIX.md (full route map, OAuth flow,
    port assignments). Done: npm run build succeeds; deployment trigger calls deployment-api; OAuth blocks unauthorized
    users; all 5 panels render. status: pending priority: P2
- id: deploy-v3-configs-cleanup-done content: > COMPLETED (2026-02-28): (1) Added auth_setup block to
  checklist.template.yaml; (2) Documented CLOUD_PROVIDER env var in cloud-providers.yaml; (3) Renamed
  checklist.unified-cloud-services.yaml → checklist.unified-trading-services.yaml; (4) Added UPI dependency to
  checklist.position-balance-monitor-service.yaml; (5) Deleted checklist.PRIORITY_SUMMARY.yaml (summary doc); (6) Added
  auth_setup_prerequisites to checklist.prerequisites.yaml. status: completed
- id: codex-root-cleanup-done content: > COMPLETED (2026-02-28): Deleted HANDOFF-DOCUMENT.md, FILE_RECOVERY_REPORT.md.
  Archived ACTUAL_VALIDATION_AUDIT_REPORT.md, END_TO_END_SYSTEM_GAP_ANALYSIS.md, REPOS-CLONED-AND-READY.md,
  SETUP-VERIFICATION.md, VALIDATION_SCRIPTS_AUDIT_REPORT.md to codex/archive/. status: completed
- id: codex-google-cloud-project-cleanup-done content: > COMPLETED (2026-02-28): Replaced all GCP_PROJECT_ID →
  GCP_PROJECT_ID across unified-trading-codex and unified-trading-deployment-v3. Replaced all central-element-323112 →
  test-project in both repos. Zero occurrences remain. status: completed
- id: codex-tier-arch-eal-uic-int-done content: > COMPLETED (2026-02-28): Added EAL (execution-algo-library), UIC_INT
  (unified-internal-contracts), MEL (matching-engine-library) to Tier 0 in 04-architecture/TIER-ARCHITECTURE.md. Added
  UDEI (unified-defi-execution-interface) and USEI (unified-sports-execution-interface) to Tier 2. Updated Phase 0 (SA
  OAuth) in 07-security/service-to-service-auth.md. status: completed
- id: ssot-corrections content: > COMPLETED (2026-02-28): Phase 3 SSOT corrections applied. Runtime topology SSOT
  entries verified and aligned: runtime-topology.yaml v6 as authoritative source, RUNTIME_TOPOLOGY_DECISIONS.md sections
  1-20 updated, 00-SSOT-INDEX.md updated with placement rationale and new SSOT entries. All cross-references from codex
  to topology YAML confirmed consistent.

# Completed: 2026-02-28

status: completed

- id: svg-regenerate content: > COMPLETED (2026-02-28): Phase 4 SVG regeneration complete.
  RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg regenerated from generate_topology_svg.py against updated runtime-topology.yaml
  v6. xmllint validation passes. Symlink at unified-trading-codex/04-architecture/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg
  confirmed pointing to unified-trading-deployment-v3/configs/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg.

# Completed: 2026-02-28

status: completed

- id: workspace-manifest-dag content: > COMPLETED (2026-02-28): Phase 5 workspace DAG generator script created and
  symlink fixed. Script: unified-trading-pm/scripts/generate_workspace_dag.py (created) Real file:
  unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg Symlink:
  unified-trading-codex/04-architecture/WORKSPACE_MANIFEST_DAG.svg ->
  ../../unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg WORKSPACE_MANIFEST_DAG.svg regenerated from
  workspace-manifest.json with corrected topological levels (UDC=L3, deployment-service/api=L6 after 2026-02-28
  restructure). All 57 repos shown across 11 levels (L0-L10). xmllint OK.

# Completed: 2026-02-28

status: completed

---

## Section Q — Quality Gate Audit Findings (2026-02-28 agent audit)

tasks:

- id: qg-central-element-test-code content: > central-element-323112 in committed test code — 5 instances. Must be
  "test-project". execution-service/tests/unit/test_preflight_checker.py:7,13,19,25 (4 lines).
  execution-service/tests/unit/test_instruction_type_algorithm_selection.py:435 (1 line). Fix: replace both files,
  quickmerge execution-service. status: pending priority: P0
- id: qg-uts-conftest-skip-pattern content: > unified-trading-services/tests/conftest.py:94,194 use file-based
  pytest.skip (blocked by gcp-auth-in-tests.mdc). conftest.py:94 — pytest.skip("GCP credentials file not found").
  conftest.py:194 — pytest.skip("GCP credentials required..."). Fix: replace with google.auth.default() pattern +
  autouse @pytest.mark.integration fixture. Reference: market-data-processing-service/tests/conftest.py has the correct
  pattern. status: pending priority: P0
- id: qg-upload-events-legacy content: > UPLOAD_STARTED / UPLOAD_COMPLETED still in 2 services — must be
  PERSISTENCE_STARTED / PERSISTENCE_COMPLETED. market-data-processing-service: data_sink.py:152,198 +
  orchestration_service.py:1025,1115 + live_mode_handler.py:346,350. instruments-service:
  cloud_instrument_storage.py:364,418. Fix: global replace in both repos, quickmerge each. status: pending priority: P0
- id: qg-unified-api-contracts-file-size content: > 3 unified-api-contracts files >900 lines (file-splitting-guide.md QG
  gate blocks merge). unified_api_contracts_external/cloud_sdks/aws_schemas.py — 1,424 lines.
  unified_api_contracts/venue_manifest.py — 1,058 lines. unified_api_contracts_external/binance/schemas.py — 1,033
  lines. Fix: split each by data type group (spot/futures/options; CeFi/DeFi/Sports; S3/SQS/IAM). status: pending
  priority: P1
- id: qg-fds-uncommitted-changes content: > features-delta-one-service has uncommitted staged changes.
  features_delta_one_service/cli/handlers/batch_handler.py + pyproject.toml modified. Fix: cd features-delta-one-service
  && bash scripts/quickmerge.sh "fix: batch handler cleanup" status: pending priority: P0
- id: qg-exec-import-error-remaining content: > execution-service: 25 remaining except ImportError in production code
  (was 214 → 130 → 25). Anti-pattern per delete-deprecated.mdc. Fix: rg "except ImportError" execution_service/ --type
  py then replace each with fail-loud import. Any requiring redesign tracked separately. Governs: delete-deprecated.mdc
  (fail loud, no try/except ImportError). Done: rg "except ImportError" execution_service/ --type py --glob '!tests/'
  returns 0 hits. status: pending priority: P0
- id: qg-venue-name-canonicalization content: > "binance" (lowercase) in 100+ production files — non-canonical per UCI
  venue constants. Same issue for "okx", "deribit", "bybit", "hyperliquid" (must be uppercase constants). Fix: rg
  '"binance"' --type py --glob '!tests/\*\*' across all services, replace with UCI venue constant import. Governs:
  no-type-any-use-specific.mdc + anti-patterns-quick-reference.mdc. Canonical constants in
  unified-config-interface/venues.py (or equivalent UCI exports). Done: rg '"binance"' --type py returns 0 hits in
  production code. status: pending priority: P1
- id: qg-type-ignore-audit content: > 100+ files have # type: ignore suppressions not documented in
  QUALITY_GATE_BYPASS_AUDIT.md. Per no-type-any-use-specific.mdc: only audited exceptions permitted. Fix: rg "# type:
  ignore" --type py --glob '!.venv\*/\*\*'. For each: fix root cause or add to QUALITY_GATE_BYPASS_AUDIT.md. Target:
  reduce to <10 documented exceptions. Governs: no-type-any-use-specific.mdc. Each bypass must be documented in
  service's QUALITY_GATE_BYPASS_AUDIT.md. Done: every # type: ignore has corresponding entry in bypass audit log.
  status: pending priority: P1
- id: qg-pip-audit-exec-services content: > pip-audit not installed in execution-service venv — blocking codex gate.
  Fix: cd execution-service && uv pip install pip-audit && bash scripts/quickmerge.sh "fix: pip-audit" Also verify
  pip-audit present in all other service venvs. status: pending priority: P0
- id: qg-exec-services-codex-18 content: > 18 residual codex violations in execution-service — quickmerge codex check
  still fails. Requires qg-pip-audit-exec-services first, then address 18 violations. Run: cd execution-service && bash
  scripts/quality-gates.sh --no-fix 2>&1 | grep "CODEX" status: pending priority: P0
- id: qg-strategy-service-gitignore content: > strategy-service dirty working tree from test artifact files (.coverage*,
  logs/\*\*/*.jsonl). Fix: add .gitignore entries: logs/\*_/_.jsonl and .coverage\*. Then: unset ENVIRONMENT && cd
  strategy-service && bash scripts/quickmerge.sh "fix: gitignore test artifacts" Note: ENVIRONMENT=production must be
  unset before quickmerge. status: pending priority: P0
- id: qg-asyncio-run-audit content: > asyncio.run() in 60+ production files — P0 runtime risk if called inside running
  event loop. Fix: rg "asynciorun" --type py --glob '!tests/\*' --glob '!.venv/\*\*' across all repos. Rule:
  asyncio.run() INSIDE async def → replace with await. In sync main() CLI entrypoint → correct, keep. Governs:
  async-http-aiohttp.mdc (never asyncio.run() inside async def). Done: zero hits of asyncio.run() inside async def in
  production code. status: pending priority: P0
- id: qg-strategy-domain-adapter-type content: > strategy-service/domain_adapter.py:89 — CloudTarget type mismatch
  (deferred as "pre-existing", not fixed). Fix root cause: check CloudTarget import source, use correct type annotation,
  no type: ignore suppression. status: pending priority: P1
- id: qg-backtest-engine-reportany content: > strategy-service/backtest_engine.py has reportAny type errors (deferred
  without fix). Part of p0-reportany-error-all-repos but specifically not yet addressed in strategy-service. Fix: rg
  "Any" strategy-service/strategy_service/ --type py then replace with specific types. Governs:
  no-type-any-use-specific.mdc (reportAny BLOCKING). Fix: replace Any with TypedDict/Protocol/dict[str,X]. Done: timeout
  120 basedpyright strategy_service/ shows 0 reportAny errors. status: pending priority: P1
- id: qg-exec-services-smoke-import content: > execution-service smoke tests failing: get_gcs_client import error. Fix:
  update smoke test to use get_storage_client() from unified-cloud-interface (UCLI). get_gcs_client was renamed/removed.
  Check UCLI exports for correct function name. Governs: external-import-standards.mdc (get_gcs_client comes from
  unified_cloud_interface, not unified_trading_services). Fix: replace from unified_trading_services import
  get_gcs_client with from unified_cloud_interface import get_storage_client. Done: python -c "from
  execution_service.smoke import \*" exits 0. status: pending priority: P0
- id: qg-strategy-service-print-pdf content: > strategy-service/export_to_pdf.py uses print() — blocked by codex gate.
  Fix: replace all print() calls with logger.info() in export_to_pdf.py. Governs: anti-patterns-quick-reference.mdc
  (print() → logger.info()). Fix: import logging; logger = logging.getLogger(**name**); replace all print() in
  export_to_pdf.py. Done: rg "^\s\*print(" strategy_service/ --type py returns 0 hits. status: pending priority: P1
- id: qg-strategy-service-tier2-dep content: > strategy-service imports a Tier 2 library class directly in service
  source (not via library wrapper). Violates services-as-orchestrators.mdc. Fix: identify T2 import, ensure used through
  proper T2 API. Governs: library-tier-architecture.mdc (services import T1/T2/T3 only via top-level, not T2 internals).
  Fix: identify which T2 lib is imported, use its public top-level API. Done: no direct imports of T2 sub-modules in
  service source. status: pending priority: P1
- id: ui-local-dev-setup content: > Add .env.local.example to each of the 11 UI repos so developers can run UIs against
  local API instances. Port assignments (from UI-DEPENDENCY-MATRIX.md): 8001=deployment-api, 8002=execution-results-api,
  8003=client-reporting-api, 8004=market-data-api. For each UI: create .env.local.example with correct VITE_API_URL +
  VITE_ENV=local; add to .gitignore: .env.local; add npm script "dev:local": "cp .env.local.example .env.local && vite"
  if not already present. UIs calling deployment-api (8001): deployment-ui, live-health-monitor-ui, batch-audit-ui,
  logs-dashboard-ui, ml-training-ui, onboarding-ui. UIs calling execution-results-api (8002): trading-analytics-ui,
  strategy-ui, execution-analytics-ui, settlement-ui. UIs calling client-reporting-api (8003): client-reporting-ui.
  Local API quickstart: cd unified-trading-deployment-v3 && uvicorn api.main:app --reload --port 8001 (or deployment-api
  after split). See: unified-trading-/codex/05-infrastructure/UI-DEPENDENCY-MATRIX.md (port table, .env.local templates,
  quickstart commands). Done: all 11 UIs have .env.local.example; npm run dev against localhost works for each UI.
  status: pending priority: P1
- id: topology-dag-codex-done content: > COMPLETED (2026-02-28): Wrote
  unified-trading-/codex/04-architecture/TOPOLOGY-DAG.md — full system topology DAG with T0-T3 library tiers, service
  pipeline layers (L1-L6), API services cluster, all 11 UIs with correct deployment-api vs execution-results-api
  routing, GCP infra, devops layer. Fixes from previous DAG: MEL→Tier0, UTS→UIC_INT/UEI edges, FOS→UDC edge, correct UI
  wiring, deployment-api shown as primary API hub, deployment-ui shown as planned standalone, UPI→PBM edge added. UI env
  routing table (dev=direct, prod=Cloud Run). Known violations table with task IDs. status: completed
- id: ic-uic-positions-modules-done content: > COMPLETED (2026-02-28): Created missing
  unified_internal_contracts/positions/ submodules required by unified-position-interface (UPI). UPI schemas.py imports
  these at startup; without them the entire UPI package fails to load. Created: positions/**init**.py, positions/cefi.py
  (CeFiPosition — spot/perp/futures/options), positions/defi_lp.py (DeFiLPPosition — Uniswap/Curve/Balancer),
  positions/defi_lending.py (DeFiLendingPosition + LendingEntry — Aave/Compound), positions/defi_staking.py
  (DeFiStakingPosition — Lido/EigenLayer). All are Pydantic v2 BaseModel with schema_version, client_id, strategy_id,
  timestamp, raw. Verified: python -c "from unified_position_interface import CanonicalPosition" exits 0. status:
  completed
- id: exec-svc-cross-svc-deps content: > ACTIVE VIOLATION: execution-service/pyproject.toml declares 3 service→service
  deps (violates Tier 4 rule — services never import from other service repos): market-data-tick-handler>=2.0.0 (via
  uv.sources market-data-tick-handler → ../market-tick-data-handler), risk-and-exposure-service>=1.0.0 (via uv.sources
  risk-and-exposure-service → ../risk-and-exposure-service), instruments-service (via uv.sources instruments-service →
  ../instruments-service). market-tick-data-handler also declares instruments-service as a dep (same violation). Fix:
  extract shared schemas from market-tick-data-handler into unified-api-contracts or a new shared-market-data-schemas
  library. Extract risk schemas into unified-internal-contracts. Remove service→service deps. Update pyproject.toml in
  execution-service and market-tick. Violations annotated in both pyproject.toml files pending this fix. status: pending
  priority: P1
- id: qg-lib-dep-docs-rewrite-done content: > COMPLETED (2026-02-28): Rewrote LIBRARY-DEPENDENCY-MATRIX.md and
  INTERNAL_DEPENDENCY_GRAPH.md. Both now cover all 16 libraries (T0-T3) and all 17 services (14 active + 3 scaffolded
  future). INTERNAL_DEPENDENCY_GRAPH.md: removed unified-order-interface (renamed to UTEI), removed
  features-delta-two-service (never existed), added UFC/UML/UDEI/USEI/UPI/MEL/URDI to graphs, added full mermaid
  service→library dependency chart, full tabular matrix, known violations table. status: completed

---

## Priority Quick-Reference

| Priority | IDs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0**   | p0-exec-results-api-types, p0-ml-bare-except, p0-strategy-live-mode, p0-cdc-tests, p0-umi-skipped-test, p0-canonical-swap-fix, p0-ui-sse, p0-reportany-error-all-repos, auth-credentials-registry, ac-ccxt-completeness, ac-fee-borrow-all-venues, ac-risk-infrastructure, ac-funding-settlement-portfolio-margin, codex-service-pair-flows-doc, codex-s2s-auth-phase0-impl, qg-central-element-test-code, qg-uts-conftest-skip-pattern, qg-upload-events-legacy, qg-fds-uncommitted-changes, qg-exec-import-error-remaining, qg-pip-audit-exec-services, qg-exec-services-codex-18, qg-strategy-service-gitignore, qg-asyncio-run-audit, qg-exec-services-smoke-import                                                                                                                                                                                       |
| **P1**   | ic-greeks-position-schema, ic-rebalance-instruction, ic-circuit-breaker-schema, ic-eod-settlement-contract, ic-feature-contracts, ic-ml-training-contracts, ic-uic-coverage-floor, ic-uic-py-typed, ic-strategy-domain-event-validation, auth-ibkr-corp-actions, ac-sentiment-oi-all-venues, ac-account-lifecycle-all-venues, ac-aggregate-trades-fills-mark-price, codex-service-dependency-diagram-v3, codex-ui-service-separation-doc, codex-orphan-repos-doc, codex-quality-gates-aws-parity, mel-deps-remove, infra-merge-utdv3, dag-mel-tier-mismatch, qg-unified-api-contracts-file-size, qg-venue-name-canonicalization, qg-type-ignore-audit, qg-strategy-domain-adapter-type, qg-backtest-engine-reportany, qg-strategy-service-print-pdf, qg-strategy-service-tier2-dep, deployment-v3-four-way-split, ui-local-dev-setup, deployment-ui-implement |
| **P2**   | ic-portfolio-risk-contracts, ic-onchain-freshness-contract, ic-onchain-per-protocol-schemas, ic-trad-fi-datasource-tag, ic-deprecated-withdraw-cleanup, ac-vol-surface-all-venues, ac-dual-structure-doc, ac-coverage-90                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

---

## Auth Items Summary

All items requiring API keys, OAuth, or Secret Manager work:

| ID                                 | What                                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| auth-credentials-registry          | Canonical secrets registry YAML                                                |
| auth-setup-secret-script           | Generalized setup_secret.sh                                                    |
| auth-secret-manager-naming         | Canonical SM naming + cursor rule                                              |
| auth-three-tranche-data-wiring     | SM tranche B (exec-odum-{venue})                                               |
| auth-ai-report-summaries           | SM anthropic-api-key                                                           |
| auth-onboarding-ui-gaps            | Google OAuth ADMIN + SM API keys                                               |
| auth-onboarding-ui-complete        | API key CRUD, SM, credentials-registry                                         |
| auth-manual-trading-consolidate    | Google OAuth submitted_by                                                      |
| auth-trading-analytics-ui          | Google OAuth TRADER                                                            |
| auth-config-promotion-workflow     | Google OAuth deployed_by                                                       |
| auth-ml-training-ui                | Google OAuth                                                                   |
| auth-deployment-service-split      | Google OAuth middleware                                                        |
| deployment-v3-four-way-split       | deployment-service + deployment-api + deployment-ui + system-integration-tests |
| auth-ibkr-corp-actions             | PENDING_CASSETTE_AWAITING_AUTH (P1)                                            |
| auth-endpoint-registry-unvalidated | CassetteStatus enum + SSOT for why venues have no VCR — NOT IN CODEBASE YET    |
| auth-sports-migration-batch1       | auth status fixes in endpoint_registry                                         |
| auth-sports-migration-batch2       | Sports UMI adapters                                                            |

---

## Citadel ML Feature Pipeline — Hardening, Deployment & Live Verification

**Prerequisite:** All items in `.cursor/plans/multi-tf_cascade_signal_architecture_3fcd8384.md` completed first. That
plan handles code, config, Terraform setup, API contract schemas, internal contracts, manifest, topology YAMLs, DAG
diagrams, unit tests. This section handles everything that requires live infrastructure.

### HFT Features — Deploy & Verify

- id: hft-feature-provision-databento content: "Provision Databento API key in Secret Manager (secret name:
  databento-api-key). Databento subscription required (~$100-500/mo) for TradFi vol surfaces (OPRA equity options, CME
  gold/NG options, CME BTC futures for gap detection). Update credentials-registry.yaml." status: pending
- id: hft-feature-provision-external-keys content: "Provision in Secret Manager: cryptopanic-api-key,
  lunarcrush-api-key, cryptoquant-api-key, coinglass-api-key. Verify FRED and Yahoo Finance free endpoints are
  accessible without keys. Update credentials-registry.yaml for each." status: pending
- id: hft-feature-deploy-services content: "Deploy updated services to Cloud Run after API keys provisioned: (1)
  features-cross-instrument-service (4Gi RAM, 2 CPU) — new service, first deployment; (2) MDPS — redeploy with new Tier
  1 HFT columns (trade*size_p10-p99, spread_volatility_15s, book_pressure_gradient, whale_trade_count,
  effective_to_quoted_spread_ratio, liq_inter_time*_, volume*clock*_); (3) market-tick-data-service — redeploy with
  OPRA, CME options, incremental_book_L2 adapters. Use quickmerge on staging branch for each." status: pending
- id: hft-feature-backfill-2024 content: "Run batch mode backfill for 2024 data after successful deploy: (1) MDPS batch
  --start-date 2024-01-01 --end-date 2024-12-31 per venue; (2) features-cross-instrument-service batch --start-date
  2024-01-01 --end-date 2024-12-31 --asset-group cefi." status: pending
- id: hft-feature-verify-lifecycle-events content: "Verify lifecycle events for features-cross-instrument-service after
  first live run: gsutil ls gs://{project}-events/features-cross-instrument-service/. Check for STARTED,
  VALIDATION_STARTED, VALIDATION_COMPLETED, PROCESSING_STARTED, PROCESSING_COMPLETED, PERSISTENCE_STARTED,
  PERSISTENCE_COMPLETED, STOPPED. No FAILED events." status: pending
- id: hft-feature-data-completeness content: "Run DataCompletionChecker for cross_instrument_features dataset 2024-01-01
  to 2024-12-31. Check NaN/inf counts, feature distributions, no missing dates. Acceptable NaN threshold: <1% per
  feature column." status: pending
- id: hft-feature-live-smoke-test content: "Live mode smoke test for features-cross-instrument-service: start with
  --mode live --asset-group cefi --feature-category regime. Verify PubSub messages on features-cross-instrument-regime
  topic within 60s. Verify GCS persistence at features/cross_instrument/regime/date=TODAY/. No errors in Cloud Logging.
  Stop service after verification." status: pending

### features-cross-instrument-service — Hardening (created 2026-02-28)

- id: fcis-quality-gates content: "Run quality gates on features-cross-instrument-service for the first time: cd
  features-cross-instrument-service && bash scripts/quickmerge.sh 'chore: initial quality gates pass' --unit-only. Fix
  all ruff/basedpyright violations found. Then run full quickmerge." status: pending
- id: fcis-integration-tests content: "Write integration tests for features-cross-instrument-service data flows using
  Layer 1 pattern (see integration-testing-layers.md): test regime calculator, cross_venue_spreads,
  realized_implied_vol, cross_asset_correlation calculators against fixture data from GCS sandbox. Use 2024-01-01 as
  test date." status: pending
- id: fcis-schema-validation content: "Run schema validation for features-cross-instrument-service output: verify all
  output columns match CrossInstrumentFeatures schema, vol*percentile*{window} columns are GONE, new binary threshold
  columns (vol_high_vs_30d, vol_low_vs_30d, rv_iv_ratio_extreme, rv_iv_inverted) are present." status: pending
- id: fcis-pubsub-verification content: "Verify PubSub topic creation and message schema for
  features-cross-instrument-service: topics features-cross-instrument-regime,
  features-cross-instrument-cross_venue_spread, features-cross-instrument-realized_vs_implied,
  features-cross-instrument-cross_asset_correlation. Verify message schema matches CrossInstrumentFeatures internal
  contract." status: pending

### features-multi-timeframe-service — Deployment & Live Verification

_(Gated on master plan completion of scaffold, calculators, and unit tests)_

- id: fmts-quality-gates content: "Run quality gates on features-multi-timeframe-service for the first time: bash
  scripts/quickmerge.sh 'chore: initial quality gates pass' --unit-only. Fix all violations. Then full quickmerge."
  status: pending
- id: fmts-deploy content: "Deploy features-multi-timeframe-service to Cloud Run after quality gates pass. Apply
  Terraform from unified-trading-deployment-v3/terraform/services/features-multi-timeframe-service/gcp/. First
  deployment — run terraform plan then terraform apply." status: pending
- id: fmts-backfill content: "Run batch backfill for features-multi-timeframe-service: --start-date 2024-01-01
  --end-date 2024-12-31 --asset-group cefi. Verify GCS output at features/multi_timeframe/{feature_category}/date=\*/"
  status: pending
- id: fmts-live-smoke-test content: "Live mode smoke test: start features-multi-timeframe-service --mode live. Verify
  PubSub messages on features-multi-timeframe-tf_momentum_alignment and features-multi-timeframe-tf_structure_context
  topics. Verify all 4 feature groups publish within 5 minutes of live startup. No errors in Cloud Logging." status:
  pending
- id: fmts-pubsub-verification content: "Verify all 4 MTF PubSub topics exist and message schemas match
  CrossTimeframeFeatures internal contract: features-multi-timeframe-tf_momentum_alignment,
  features-multi-timeframe-tf_structure_context, features-multi-timeframe-tf_vol_compression,
  features-multi-timeframe-tf_session_context." status: pending

### ML Pipeline — Feature Integration Verification

_(Gated on both services above being live and backfilled)_

- id: ml-mtf-feature-subscription-verify content: "Verify ml-training-service can read cross-instrument and
  multi-timeframe features from GCS for a training run. Run ml-training-service batch for a single instrument (BTC, 4h
  timeframe) with all 22+ feature groups subscribed. Confirm no KeyError or missing column errors. Check SHAP output
  includes features from new groups." status: pending
- id: ml-cascade-live-verify content: "After CascadeInferenceMode is implemented and ml-inference-service deployed:
  verify CascadePredictionEvent messages appear on the cascade-predictions PubSub topic. Confirm strategy-service
  receives and processes them without error." status: pending
- id: tier-restructure-conflict-policy status: completed date: 2026-02-28 content: | Tier level restructure completed
  2026-02-28. New structure: L0-L10 (11 levels). KEY CHANGES:
  - deployment-api, deployment-service: L0 → L6 (own tier between foundational services L5 and bulk services L7)
  - All former L6 services (features-\*, alerting, execution, MDPS, ML inference, PnL, strategy): L6 → L7
  - Former L7 (API gateways + PBM/risk/strategy-validation): L7 → L8
  - Former L8 (all UIs): L8 → L9
  - unified-trading-deployment-v3: L6 → L10 (IaC; must deploy last — references all service images)
  - system-integration-tests: L0 → L10 (runs after full deploy) CONFLICT POLICY: If any plan, README, or pyproject.toml
    references old merge_level values, FIX THEM — do NOT skip. Stale tier refs cause quickmerge cascade to run in wrong
    order. QUICKMERGE NOTE: quickmerge.sh has no hardcoded level numbers — safe. No changes needed. Quality gates run
    per-repo regardless of level; level only affects cascade order. STALE REFS KNOWN AT TIME OF RESTRUCTURE (fix when
    encountered):
  - multi-tf_cascade_signal_architecture_3fcd8384.md: mentions merge_level=6 for FMTS (now L7)
  - hft_feature_pipeline_integration_70995051.md: mentions merge_level=6 for FCIS (now L7)
  - manifest_svg_checklist_alignment_8c9891ba.md: mentions deployment-service/api to L5 (now L6)
  - Any pyproject.toml or README that says "merge_level: 6" for feature services → update to 7
  - Any pyproject.toml or README that says "merge_level: 8" for UI repos → update to 9 SVG GENERATION:
  - WORKSPACE_MANIFEST_DAG.svg: regenerate with `python3 unified-trading-pm/scripts/generate_workspace_dag.py`
  - RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg: separate architectural layer labels (L1-L7), NOT affected by build tiers
