---
name: Config, Reporting & UI Completion
overview: "Canonical config schemas (Strategy/Execution/Backtest/ML), automated client reporting system migrating mr_report to proper client-reporting-service (NEW standalone repo) + client-reporting-ui, UI restructuring (Google OAuth everywhere, settlement-ui repurpose, service/UI strict separation), RBAC across all UIs, credentials-registry.yaml creation, reportAny=error across all repos. Institutional-grade A+ audit standard. Addendum to End-to-End Completion Master Plan v2."
todos:
  - id: reportany-error-all-repos
    content: "Upgrade reportAny from 'warning' to 'error' in ALL repos where it is currently 'warning': unified-internal-contracts, unified-trading-services, alerting-system, unified-cloud-interface, unified-reference-data-interface, ml-inference-service, market-tick-data-handler, execution-algo-library, features-delta-one-service, market-data-processing-service, unified-feature-calculator-library, api-contracts, unified-position-interface, unified-ml-interface, unified-trade-execution-interface, strategy-service, instruments-service. Update both pyproject.toml [tool.basedpyright] and pyrightconfig.json in each repo. Run timeout 120 basedpyright <src>/ per repo and fix all surfaced Any-type violations before moving on."
    status: pending
  - id: credentials-registry-create
    content: "Create execution-services/configs/credentials-registry.yaml: canonical mapping of client_id → secret_name pattern, tranche, venue, currency, introducer_id. Clients: PR (exec-pr-okx-usdt, tranche=managed, introducer=max), NN (exec-nn-okx-usdt, tranche=managed), ET (exec-et-binance-usdt, tranche=managed, introducer=bluecoast), STD (exec-std-okx-usdt, tranche=managed), GP (exec-gp-okx-usdt, tranche=managed), SL/SL2 (tranche=managed), ANU (tranche=managed), IK (tranche=managed, pooled=true), YOAV (tranche=fund_of_fund, currency=BTC), GUY_ASRAF (tranche=fund_of_fund, currency=BTC). Secret names follow canonical pattern exec-{client_id}-{venue}-{account_type} (e.g. exec-odum-binance-futures for own accounts, exec-pr-okx-usdt for managed client PR) — service checks Secret Manager for existence and warns if missing."
    status: completed
  - id: config-schemas-uic
    content: "Create unified_internal_contracts/configs/__init__.py, strategy.py, execution.py, backtest.py, ml_training.py. Exact schemas as defined in Part 1. Use BaseContractModel (frozen=True, schema_version Literal['v1']). No Any types — reportAny=error enforced. Export all from configs/__init__.py and add to top-level unified_internal_contracts/__init__.py __all__. Run timeout 120 basedpyright unified_internal_contracts/ and fix all errors. Run bash scripts/quickmerge.sh 'feat: add canonical config schemas'."
    status: completed
  - id: reporting-schemas-uic
    content: "Create unified_internal_contracts/reporting/__init__.py, client.py (FeeStructure, HighWaterMark, ClientPerformanceRecord, ClientInvoice, MonthlyReport). Exact schemas as defined in Part 2. Real client fee structures: PR=40% odum/10% trader/max 15% introducer, NN=30%/10%, ET=30%/10%/bluecoast 5%, STD=35%/10%, IK=35%/10%, underwater accounts accrue $50/month server costs. All Decimal fields for monetary values. Export and quickmerge."
    status: completed
  - id: client-onboarding-schema
    content: "Create unified_internal_contracts/client/__init__.py, onboarding.py (ClientOnboardingStatus). Fields: client_id, aml_score Optional[float] (<50=pass), aml_checked_at, kyc_docs_received, ima_signed, ima_signed_at, fee_structure_set, hwm_initialized, api_key_added, test_transaction_confirmed, is_live, created_at. Export and quickmerge."
    status: completed
  - id: manual-instruction-schema
    content: "Create unified_internal_contracts/execution/__init__.py, manual.py (ManualInstruction). Fields: instruction_id, submitted_by (Google OAuth sub claim), venue, account_id, instrument_key, side BUY|SELL, order_type, quantity Decimal, price Optional[Decimal], reason str (required for FCA audit trail), submitted_at datetime. Export and quickmerge. Then update execution-services/execution_services/api/manual_instruction_api.py to validate incoming POST /manual/instruction body against ManualInstruction UIC schema and add submitted_by from Google OAuth token claims."
    status: completed
  - id: client-reporting-service-new-repo
    content: "Create NEW standalone repo client-reporting-service following new-repo-setup.mdc workflow: gh repo create IggyIkenna/client-reporting-service --private --clone, grant team access (CosmicTrader datado), scaffold with ServiceCLI pattern + FastAPI layer (this service IS user-facing so FastAPI is required). Dependencies: fastapi>=0.109, uvicorn[standard], unified-internal-contracts, unified-trading-services, unified-config-interface, unified-events-interface, jinja2>=3.0, matplotlib>=3.9, anthropic>=0.40 (for AI summaries), google-cloud-secret-manager (via unified-cloud-interface). Structure: client_reporting_service/api/main.py (FastAPI app with Google OAuth middleware), client_reporting_service/core/fee_calculator.py (FeeCalculator class migrated from mr_report), client_reporting_service/core/report_generator.py (HTML generation via Jinja2), client_reporting_service/core/tranche_router.py (routes A/B/C data sources), client_reporting_service/config.py (extends UnifiedCloudConfig). Update workspace-manifest.json and uv pip install -e client-reporting-service/ from workspace root."
    status: completed
  - id: mr-report-migration
    content: "Migrate mr_report logic into client-reporting-service. Source: /Users/ikennaigboaka/Documents/repos/other_repos/mr_report/. (1) Copy odum_mr_executive_summary_html_css_template_gold_black.html to client-reporting-service/client_reporting_service/templates/odum_executive_summary.html. Copy january/november/december BTC report templates to templates/btc_investor_note.html. (2) Migrate FeeCalculator from create_invoice_tracker.py: dual HWM logic (trader HWM=10% above trader HWM, odum HWM per client percentage), introducer fee calculation (PR: max gets 15% of all historical odum collections; ET: bluecoast gets 5%), server costs $50/month per underwater account. (3) Migrate chart generation from build_report.py: matplotlib monthly returns bar chart, cross-exchange comparison table, embed as base64 data URIs in HTML. (4) Migrate data.csv schema validation. Archive mr_report by adding ARCHIVED.md notice. Do NOT delete — keep as reference. Run quickmerge in client-reporting-service."
    status: completed
  - id: reporting-backend-api
    content: "Build client-reporting-service FastAPI endpoints with Google OAuth (verify Bearer token via google-auth library, check hd claim for domain restriction). Endpoints: GET /reports/{client_id} → list[MonthlyReport] (filtered by client_id from OAuth token for CLIENT role), GET /reports/{client_id}/{period_month} → MonthlyReport, POST /reports/generate (ADMIN role, body: {client_id, period_month, dry_run}) → triggers report generation pipeline, GET /reports/{report_id}/html → serve HTML from GCS, GET /invoices/{client_id}/pending → list[ClientInvoice], PATCH /invoices/{invoice_id}/mark-paid body:{tx_hash} (COMPLIANCE role), GET /clients/{client_id}/hwm → HighWaterMark, GET /health. Store reports to GCS via get_storage_client() from unified-cloud-interface. Index MonthlyReport metadata in GCS JSON sidecar. FCA 5-year retention: use GCS object lifecycle policy retention_period=5y. Run quickmerge."
    status: done
    completed_at: "2026-02-27"
  - id: three-tranche-data-wiring
    content: "Wire three data sources in client_reporting_service/core/tranche_router.py. Tranche A (fund_of_fund — YOAV, GUY_ASRAF): data_source='manual', accept CSV upload via POST /reports/upload-tranche-a body:{client_id, period_month, csv_content base64}. CSV columns: date, aum_btc, return_pct. No API keys required. Tranche B (managed — PR, NN, ET, STD, GP, SL, SL2, ANU, IK): data_source='api_live', read secret exec-odum-{venue}-{account_type} from Secret Manager via get_secret() from unified-cloud-interface, instantiate position reader, pull closing balance and fills for period_month. Canonical secret name lookup from credentials-registry.yaml. If secret missing: log warning, fall back to data_source='api_static' and require manual balance input. Tranche C (own — Odum internal): data_source='api_live', read directly from position-balance-monitor-service API and pnl-attribution-service API."
    status: pending
  - id: ai-report-summaries
    content: "Add AI executive summary generation to client_reporting_service/core/ai_summary.py. Use anthropic SDK (claude-3-5-haiku — fast and cheap for summaries). Prompt template: system='You are an institutional fund manager writing a monthly performance note for a client. Be professional, concise, data-driven.' user=f'Client {client_id}, Period {period_month}, AUM {closing_aum} {currency}, PnL {pnl} ({return_pct:.2f}%), Sharpe (annualized) {sharpe}, Max Drawdown {max_dd}%, Key events: {market_context}. Write a 3-paragraph executive summary.' Store in MonthlyReport.ai_summary. API key from Secret Manager key name anthropic-api-key via unified-cloud-interface get_secret(). If secret missing or API fails: log warning, set ai_summary=None, continue (non-blocking)."
    status: pending
  - id: google-oauth-shared-middleware
    content: "Create shared Google OAuth middleware for all FastAPI services. Add to unified-trading-services/unified_trading_services/auth/google_oauth.py: GoogleOAuthMiddleware class that (1) reads Authorization: Bearer {token} header, (2) verifies token via google.oauth2.id_token.verify_oauth2_token(), (3) checks hd claim = configured domain (GOOGLE_OAUTH_DOMAIN env via UnifiedCloudConfig), (4) extracts sub, email, groups claims, (5) attaches to request.state.user. Add get_current_user() FastAPI dependency. Add role_required(role: str) dependency that checks request.state.user.groups. VITE_SKIP_AUTH=true bypass for local dev (already in most UIs). Local dev: use GOOGLE_OAUTH_DOMAIN='' to skip domain check. Add to unified-trading-services pyproject.toml: google-auth>=2.40.0. Quickmerge unified-trading-services."
    status: completed
  - id: auth-rbac-all-uis
    content: "Replace Okta auth with Google OAuth in ALL UIs. Each UI already has VITE_SKIP_AUTH pattern — preserve it. (1) Remove @okta/okta-auth-js and @okta/okta-react from ALL UI package.json files. (2) Add google-auth-library or use native fetch for Google OAuth flow. (3) Create shared src/auth/GoogleAuth.tsx component: uses Google OAuth2 implicit flow, stores id_token in sessionStorage (NOT localStorage — security), attaches as Bearer token to all API calls. (4) Create src/auth/RequireAuth.tsx: checks sessionStorage for valid token, redirects to /login if missing or expired. (5) live-health-monitor-ui: add RequireAuth wrapper (TRADER role minimum). (6) settlement-ui: add RequireAuth wrapper (COMPLIANCE role). (7) onboarding-ui: ADMIN role. (8) client-reporting-ui: CLIENT role — filter by sub claim = client_id. (9) All shell UIs (backtest-ui, trading-analytics-ui, batch-audit-ui, logs-dashboard-ui): add RequireAuth (ANALYST minimum). VITE_GOOGLE_CLIENT_ID env var. npm install in each UI, run typecheck, quickmerge per UI repo."
    status: done
    completed_at: "2026-02-27"
  - id: service-ui-separation-audit
    content: "Audit and enforce strict service/UI separation across all repos. RULE: services (Python) have NO UI dependencies. UIs (React/TypeScript) are separate repos that call service APIs. Check and fix: (1) unified-trading-deployment-v3 currently co-locates FastAPI backend + React UI in same repo — KEEP as-is (it is user-facing deployment control plane, FastAPI is correct here, UI is in ui/ subdir which is acceptable). (2) strategy-service: CLI only, no FastAPI — CORRECT, no change needed. (3) execution-results-api: FastAPI backend serving backtest-ui — CORRECT separation, keep. (4) risk-and-exposure-service: has api/main.py FastAPI — this is the internal pre-trade API, NOT user-facing. Remove FastAPI from risk-and-exposure-service (it should publish alerts via unified-events-interface to alerting-system, not serve HTTP). Pre-trade checks should be called as library imports within execution-services, not HTTP. (5) position-balance-monitor-service api/main.py: keep — this IS user-facing (position data for UIs). (6) Any other service with FastAPI that is not user-facing: remove FastAPI, use unified-events-interface for outputs."
    status: pending
  - id: client-reporting-ui-build
    content: "Build out client-reporting-ui from current shell (has Okta stub, package.json with @okta deps). (1) Remove @okta deps, add Google OAuth (see auth-rbac-all-uis todo). (2) Add react-router-dom, recharts, axios. (3) Pages: /login (Google OAuth button), /reports (list MonthlyReport cards for authenticated client, filtered by client_id from token), /reports/:period (HTML iframe viewer — load GET /reports/{id}/html from client-reporting-service), /invoices (list ClientInvoice, show pending/paid status), /invoices/:id (detail + payment hash input field, COMPLIANCE role only), /performance (recharts LineChart of return_pct by period_month, polling GET /clients/{id}/hwm every 30s for live AUM). (4) API client: src/api/reportingClient.ts calls client-reporting-service base URL (VITE_REPORTING_SERVICE_URL env). (5) npm run typecheck must pass. quickmerge client-reporting-ui."
    status: done
    completed_at: "2026-02-27"
  - id: settlement-ui-repurpose
    content: "Repurpose settlement-ui from ManualTrading duplicate to Fund Settlement & Invoicing UI. (1) Remove ManualTradingControls.tsx, ManualTradingPanel.tsx, useManualTradingForm.ts, src/api/manualTrading.ts — they duplicate live-health-monitor-ui. (2) Remove Recharts (will re-add if needed). (3) Add react-router-dom, axios, @tanstack/react-table. (4) Add Google OAuth RequireAuth (COMPLIANCE role). (5) Build pages: /positions (EOD position snapshot table, calls position-balance-monitor-service GET /positions, columns: client_id, strategy_id, venue, instrument, quantity, avg_price, unrealized_pnl, reconciliation status), /reconciliation (position vs expected diff table, calls GET /reconciliation/status, trigger button calls POST /reconciliation/trigger), /invoices (ClientInvoice table from client-reporting-service, mark-paid flow with tx_hash input), /reports (MonthlyReport browser, link to HTML view), /hwm (HighWaterMark history per client, GET /clients/{id}/hwm). (6) npm run typecheck. quickmerge settlement-ui."
    status: completed
  - id: backtest-ui-build
    content: "Build backtest-ui from current shell (has Okta stub). (1) Replace Okta with Google OAuth RequireAuth (ANALYST read, ADMIN for promote-to-live). (2) Add react-router-dom, recharts, axios. (3) Pages: /grids (list BacktestGridConfig run_ids from execution-results-api GET /api/v1/results, group by run_id), /grids/:runId (recharts Heatmap — x=param1 values, y=param2 values, color=objective_metric value, use recharts ScatterChart or custom SVG grid), /grids/:runId/best (BacktestGridResult best cell: sharpe, calmar, total_return_pct, max_drawdown_pct, win_rate, n_trades; promote-to-live button — POST to execution-results-api /api/v1/config/promote body:{cell_id, run_id, target_strategy_id}, ADMIN role only), /configs/live (list current StrategyConfig per strategy from execution-results-api GET /api/v1/config/sources), /configs/:strategyId/history (config_version history). (4) npm run typecheck. quickmerge backtest-ui."
    status: completed
  - id: trading-analytics-ui-build
    content: "Build trading-analytics-ui from current shell (has Okta stub + VITE_SKIP_AUTH pattern). (1) Replace Okta with Google OAuth RequireAuth (TRADER role). (2) Add react-router-dom, recharts, axios, eventsource-polyfill. (3) Pages: /positions (live positions table, SSE from position-balance-monitor-service GET /stream/positions — update rows in-place on each SSE event), /pnl (recharts BarChart PnL breakdown: group by instrument, by underlying, by strategy — data from pnl-attribution-service REST GET /pnl/{client_id}?period=MTD), /executions (live fills feed, SSE from execution-results-api GET /stream/fills, scrolling table), /risk (risk metrics panel: Greeks exposure for options, VaR 1d/5d, margin health bar — data from risk-and-exposure-service REST GET /exposure/summary), /orderbook (see monitoring plan), /latency (see monitoring plan). (4) npm run typecheck. quickmerge trading-analytics-ui."
    status: pending
  - id: manual-trading-consolidate
    content: "Consolidate manual trading to live-health-monitor-ui only. (1) settlement-ui: already removed in settlement-ui-repurpose todo. (2) In live-health-monitor-ui ManualTradingPanel.tsx: add submitted_by field (read from Google OAuth sessionStorage token sub claim), add reason textarea (required, min 10 chars, FCA audit requirement), add cancel/amend buttons that call new API endpoints. (3) In execution-services manual_instruction_api.py: add POST /manual/cancel body:{instruction_id, reason} and POST /manual/amend body:{instruction_id, new_quantity, new_price, reason}. Validate all bodies against ManualInstruction UIC schema. Add submitted_by from Google OAuth Bearer token claims (use GoogleOAuthMiddleware from unified-trading-services). Log every manual instruction submission/cancel/amend as unified-events-interface log_event. quickmerge execution-services and live-health-monitor-ui."
    status: pending
  - id: onboarding-ui-gaps
    content: "Complete onboarding-ui to match real KYC workflow. (1) Add Google OAuth RequireAuth (ADMIN role — onboarding is admin-only). (2) Add AMLScreening.tsx page at /aml-screening: wallet address input, calls onboarding-service (or placeholder REST endpoint) POST /aml/screen body:{wallet_address, client_id}, shows score badge (green <50, red >=50), stores result in ClientOnboardingStatus.aml_score. (3) Add FeeStructureConfig.tsx page at /fee-structure: form fields for odum_fee_pct, trader_fee_pct, introducer_id, introducer_fee_pct per client_id, saves to GCS via onboarding-service POST /clients/{id}/fee-structure, updates ClientOnboardingStatus.fee_structure_set=true. (4) Add HWMInitialization.tsx page at /hwm-init: opening_balance (Decimal), currency (USDT|BTC), hwm_date (date picker), venue, saves HighWaterMark via client-reporting-service POST /clients/{id}/hwm. (5) APIKeyManagement.tsx: wire to Secret Manager via onboarding-service POST /clients/{id}/api-key body:{venue, api_key (encrypted), api_secret (encrypted)}, canonical secret name = exec-odum-{venue}-{account_type}. (6) AuditLog.tsx: wire to GET /audit/events?entity_id={client_id} from onboarding-service. (7) VenueOnboarding.tsx: add document checklist (cert of incorporation, UBO docs, exchange onboarding form). (8) StrategyOnboarding.tsx: wire to StrategyConfig — GET /configs/{strategy_id} from execution-results-api. (9) Update App.tsx to add new routes. npm run typecheck. quickmerge onboarding-ui."
    status: pending
  - id: sse-endpoints-add
    content: "Add SSE endpoints using sse-starlette to existing FastAPI services. (1) execution-results-api: add sse-starlette>=1.6.1 to pyproject.toml. Add GET /stream/fills route in api/routes/fills_stream.py: subscribes to internal fills queue (asyncio.Queue fed by execution-services via unified-events-interface), yields FillEventPubSubPayload events as SSE. (2) position-balance-monitor-service: add sse-starlette. Add GET /stream/positions route: yields PositionUpdateMessage events when positions change, streams JSON of PositionResponse. Use asyncio background task to poll position_tracker.get_all_positions() every 2s and push deltas. (3) Add Google OAuth verification to SSE endpoints (same GoogleOAuthMiddleware). (4) Test with curl -N -H 'Authorization: Bearer {token}' http://localhost:8000/stream/positions. quickmerge both repos."
    status: completed
  - id: config-promotion-workflow
    content: "Wire BacktestGridResult → StrategyConfig promotion flow. (1) In execution-results-api add POST /api/v1/config/promote endpoint: body={cell_id, run_id, target_strategy_id, deployed_by (from OAuth token email)}. Loads BacktestGridResult for cell_id, creates StrategyConfig with signal_params=BacktestGridResult.cell_config.param_grid, promoted_from_backtest_run_id=run_id, config_version bumped via ConfigStore. Stores to GCS via ConfigStore(bucket, strategy_id). Returns new StrategyConfig. (2) In execution-services instruction_api.py: on startup, load active StrategyConfig from ConfigStore instead of ad-hoc dict. Watch for config version changes (poll ConfigStore every 30s in background task, reload if config_version changed). (3) Add promoted_from_backtest_run_id to StrategyConfig.deployed_by audit log entry. quickmerge execution-results-api and execution-services."
    status: pending
  - id: ml-training-config-wire
    content: "Wire MLTrainingConfig UIC schema into ml-training-service. (1) In ml-training-service: add unified-internal-contracts dependency to pyproject.toml (uv add). (2) In ml-training-service CLI handler: before run, construct MLTrainingConfig from CLI args (run_id=uuid4(), model_type, hyperparams dict, feature_set list, training/validation dates, target). Store to ConfigStore(bucket='ml-store', service_name=f'ml-training/{model_type}'). (3) After training completes: store BacktestGridResult equivalent (MLTrainingResult — add to UIC unified_internal_contracts/configs/ml_training.py: MLTrainingResult with metrics sharpe/calmar/val_loss/accuracy). (4) ml-deployment-ui (ML analysis UI — NOT the deployment orchestration UI) should read MLTrainingConfig and MLTrainingResult from ConfigStore via ml-training-service API. quickmerge ml-training-service."
    status: pending
  - id: ml-deployment-ui-scope-correct
    content: "Clarify and build ml-deployment-ui as ML Analytics & Deployment UI (NOT the system deployment UI). ml-deployment-ui scope: (1) /experiments — list MLTrainingConfig run_ids from ml-training-service API GET /experiments. (2) /experiments/:runId — MLTrainingResult metrics: val_loss, accuracy, sharpe, feature_importance chart (recharts BarChart), compare vs baseline. (3) /experiments/:runId/deploy — deploy best model to ml-inference-service: POST /experiments/{id}/deploy body:{target_env: live|staging}, ADMIN role only. (4) /models — list deployed ModelMetadata from ml-inference-service GET /models. (5) /models/:modelId/ab-test — configure A/B split %, start/stop A/B test. Replace Okta with Google OAuth. Add react-router-dom, recharts. npm run typecheck. quickmerge ml-deployment-ui."
    status: pending
  - id: strategy-ui-new-repo
    content: "Create new strategy-ui repo (strategy-service has no UI — gap identified). gh repo create IggyIkenna/strategy-ui --private --clone. Scaffold as React/Vite/TypeScript UI following new-repo-setup.mdc UI scaffold pattern. Dependencies: react, react-dom, react-router-dom, recharts, axios, tailwindcss, typescript, vite, playwright. Google OAuth RequireAuth (ANALYST read, ADMIN for config write). Pages: /strategies (list strategy_id + status + last_run from strategy-service API), /strategies/:id (strategy config detail: StrategyConfig fields, signal_params, capital_usd, risk_limits), /strategies/:id/backtest (trigger backtest via strategy-service: POST /strategies/{id}/run-backtest body:{start_date, end_date}, shows BacktestGridResult cards), /strategies/:id/live (live execution status, current positions from position-balance-monitor-service). strategy-service needs a thin FastAPI layer added (api/main.py) to serve these endpoints — add fastapi, uvicorn to strategy-service pyproject.toml [project.optional-dependencies] api = [...]. quickmerge both repos."
    status: done
    completed_at: "2026-02-27"
  - id: fill-tracking-system
    content: "Build fill tracking system in execution-results-api"
    status: done
    completed_at: "2026-02-27"
  - id: pnl-6-dimension-schema
    content: "Add GreeksExposure and PnLBreakdown schemas to UIC"
    status: done
    completed_at: "2026-02-27"
  - id: pnl-6-dimension-engine
    content: "Wire PnL 6-dimension into pnl-attribution-service"
    status: done
    completed_at: "2026-02-27"
  - id: enterprise-kill-switch
    content: "Kill switch endpoint, rate limiting, GCS audit persistence"
    status: done
    completed_at: "2026-02-27"
  - id: venue-names-canonical
    content: "Fix non-canonical venue names (100+ instances)"
    status: partial
    notes: "Fixed ~20 in URDI adapters and key files. 80+ remain in test fixtures and legacy code."
  - id: type-ignore-audit
    content: "Audit 309 type:ignore suppressions - QUALITY_GATE_BYPASS_AUDIT.md created"
    status: done
    completed_at: "2026-02-27"
  - id: hardcoded-project-ids
    content: "Remove hardcoded central-element project IDs from ~10 production files"
    status: done
    completed_at: "2026-02-27"
  - id: datetime-naive-fix
    content: "Fix datetime.now() naive (7 files)"
    status: done
    completed_at: "2026-02-27"
  - id: importerror-fallbacks
    content: "Fix except ImportError fallbacks (~130 files)"
    status: pending
    priority: medium
  - id: large-file-splits
    content: "Split large files: engine.py (2826L), aws_schemas.py (1424L), venue_manifest.py (1058L), binance/schemas.py (1033L)"
    status: pending
    priority: low
  - id: type-ignore-arch-violations
    content: "Fix 67 architectural type:ignore violations identified in audit"
    status: pending
    priority: high
isProject: false
---

# Config, Reporting & UI Completion Plan

Addendum to: `end-to-end_completion_master_plan_(v2)_2ce484e2.plan.md`

**Updated:** 2026-02-27 — Incorporates full answers on auth (Google OAuth replacing Okta), service/UI separation, client data from mr_report, credentials-registry.yaml creation, reportAny=error mandate, client-reporting-service as new standalone repo, ML deployment UI correct scoping.

---

## Workspace Rules (Every Agent Must Follow)

```
- uv not pip
- bash scripts/quickmerge.sh "message" not git push
- timeout 120 basedpyright <source_dir>/ not basedpyright .
- from unified_events_interface import setup_events, log_event — no fallbacks
- No os.getenv() — use UnifiedCloudConfig
- No Any types — reportAny = "error" everywhere
- No try/except ImportError — fail loud
- Delete deprecated code — no parallel code paths
- Search unified libraries before implementing anything new
- typeCheckingMode = "strict" in pyrightconfig.json
```

---

## Part 0 — Cross-Cutting Prerequisites

### P0.1 — reportAny = "error" Mandate

**Decision**: `reportAny = "error"` in ALL repos. Non-negotiable for institutional audit standard.

Repos currently on `"warning"` that must be upgraded (15 repos):

| Repo | Current | Target |
|------|---------|--------|
| unified-internal-contracts | warning | **error** |
| unified-trading-services | not set | **error** |
| alerting-system | warning | **error** |
| unified-cloud-interface | warning | **error** |
| unified-reference-data-interface | warning | **error** |
| ml-inference-service | warning | **error** |
| market-tick-data-handler | warning | **error** |
| execution-algo-library | warning | **error** |
| features-delta-one-service | warning | **error** |
| market-data-processing-service | warning | **error** |
| unified-feature-calculator-library | warning | **error** |
| api-contracts | warning | **error** |
| unified-position-interface | warning | **error** |
| unified-ml-interface | warning | **error** |
| unified-trade-execution-interface | warning | **error** |
| strategy-service | warning | **error** |
| instruments-service | warning | **error** |

For each repo: edit `pyproject.toml` `[tool.basedpyright]` section AND `pyrightconfig.json`. Then `timeout 120 basedpyright <src>/` and fix all `reportAny` violations. Then `quickmerge`.

### P0.2 — credentials-registry.yaml

**File**: `execution-services/configs/credentials-registry.yaml`

```yaml
# Canonical client → secret mapping.
# Secret name pattern: exec-{client_id}-{venue}-{account_type}
# Examples: exec-odum-binance-futures (own), exec-pr-okx-usdt (managed client PR)
# Service checks Secret Manager for existence and warns if missing.
clients:
  PR:
    full_name: "Prism Capital"
    tranche: managed
    currency: USDT
    venue: okx
    secret_name: exec-pr-okx-usdt
    odum_fee_pct: 0.40
    trader_fee_pct: 0.10
    introducer_id: max
    introducer_fee_pct: 0.15   # 15% of all historical odum collections
    is_active: true

  NN:
    full_name: "Namnar"
    tranche: managed
    currency: USDT
    venue: okx
    secret_name: exec-nn-okx-usdt
    odum_fee_pct: 0.30
    trader_fee_pct: 0.10
    is_active: true

  ET:
    full_name: "Eqvilent"
    tranche: managed
    currency: USDT
    venue: binance
    secret_name: exec-et-binance-usdt
    odum_fee_pct: 0.30
    trader_fee_pct: 0.10
    introducer_id: bluecoast
    introducer_fee_pct: 0.05   # 5% of all historical odum collections
    is_active: true

  STD:
    full_name: "Steady Hash"
    tranche: managed
    currency: USDT
    venue: okx
    secret_name: exec-std-okx-usdt
    odum_fee_pct: 0.35
    trader_fee_pct: 0.10
    is_active: true

  GP:
    full_name: "GPD Capital"
    tranche: managed
    currency: USDT
    venue: okx
    secret_name: exec-gp-okx-usdt
    odum_fee_pct: 0.30
    trader_fee_pct: 0.10
    is_underwater: true
    is_active: true

  SL:
    full_name: "Shaun Lim"
    tranche: managed
    currency: USDT
    venue: okx
    secret_name: exec-sl-okx-usdt
    odum_fee_pct: 0.30
    trader_fee_pct: 0.10
    is_underwater: true
    is_active: true

  SL2:
    full_name: "Shaun Lim 2"
    tranche: managed
    currency: BTC
    venue: okx
    secret_name: exec-sl2-okx-btc
    odum_fee_pct: 0.30
    trader_fee_pct: 0.10
    is_underwater: true
    is_active: true

  ANU:
    full_name: "Anu"
    tranche: managed
    currency: BTC
    venue: okx
    secret_name: exec-anu-okx-btc
    odum_fee_pct: 0.30
    trader_fee_pct: 0.10
    is_underwater: true
    is_active: true

  IK:
    full_name: "IK Pooled"
    tranche: managed
    currency: USDT
    venue: okx
    secret_name: exec-ik-okx-usdt
    odum_fee_pct: 0.35
    trader_fee_pct: 0.10
    is_pooled: true
    pool_investors:
      jihane: 0.25344
      amaka: 0.216
      ik: 0.53056
    is_underwater: true
    is_active: true

  YOAV:
    full_name: "Yoav"
    tranche: fund_of_fund
    currency: BTC
    data_source: manual
    odum_fee_pct: 0.20
    trader_fee_pct: 0.00
    is_active: true

  GUY_ASRAF:
    full_name: "Guy Asraf"
    tranche: fund_of_fund
    currency: BTC
    data_source: manual
    odum_fee_pct: 0.20
    trader_fee_pct: 0.00
    is_active: true

server_costs_per_underwater_account_usd: 50
```

### P0.3 — Service/UI Separation Rules

**RULE**: Services (Python) run without UI dependencies. UIs (React/TypeScript) are separate repos calling service APIs via HTTP. FastAPI is **only** added to a service when it is user-facing or externally consumed.

| Repo | FastAPI Correct? | Action |
|------|-----------------|--------|
| execution-results-api | ✅ Yes — UI-facing backtest API | Keep |
| execution-services api/manual_instruction_api.py | ✅ Yes — UI-facing manual trade | Keep |
| position-balance-monitor-service api/main.py | ✅ Yes — UI-facing position data | Keep |
| risk-and-exposure-service api/main.py | ❌ No — internal pre-trade checks, not user-facing | Remove FastAPI, pre-trade checks called as library import in execution-services |
| alerting-system | ✅ Yes — external SSE/webhook delivery | Keep + build out |
| unified-trading-deployment-v3 api/ | ✅ Yes — deployment control plane | Keep |
| strategy-service | ❌ No FastAPI currently — correct | Add optional api/ only when strategy-ui needs it |
| All features-* services | ❌ No — batch CLI only | Correct, no change |
| ml-training-service | ❌ No — batch CLI only | Correct, add optional api/ for ml-deployment-ui |
| market-tick-data-handler | ❌ No — publishes to Pub/Sub | Correct, order book SSE lives in new market-data-api repo |

---

## Part 1 — Canonical Config Schemas

### The gap

Config versioning exists in ConfigStore (`schema-v{N}/config-v{timestamp}`) and GCS (`V{version}/{strategy_base}/`) but there are no UIC canonical Pydantic schemas for any config type. `execution-results-api/api/routes/config.py` has `GenerateConfigRequest` but returns 501 Not Implemented — grid generation wired to execution-services which has no UIC schema either.

### New schemas: `unified_internal_contracts/configs/`

All models use `BaseContractModel` (frozen=True, `model_config = {"frozen": True}`). No `Any` types — `reportAny = "error"` enforced.

```python
# configs/strategy.py
class StrategyConfig(BaseContractModel):
    """Live deployment config — the single source of truth deployed to execution."""
    schema_version: Literal["v1"] = "v1"
    config_version: int                        # monotonically increasing per strategy
    strategy_id: str
    client_id: str
    is_live: bool = True
    instruments: list[str]                     # canonical instrument keys
    venue_accounts: list[str]                  # VenueAccount.account_id refs
    capital_usd: Decimal
    max_position_usd: Decimal
    risk_limits: RiskLimits                    # inline sub-schema from UIC risk.py
    execution_algo: str                        # "TWAP" | "VWAP" | "MARKET"
    signal_params: dict[str, float]            # strategy-specific signal parameters
    promoted_from_backtest_run_id: str | None = None   # audit traceability
    deployed_at: datetime
    deployed_by: str                           # Google OAuth email of deployer

class ExecutionConfig(BaseContractModel):
    """Per-venue execution parameters."""
    schema_version: Literal["v1"] = "v1"
    config_version: int
    strategy_id: str
    venue: str
    account_id: str
    order_type: str                            # "LIMIT" | "POST_ONLY" | "MARKET"
    slippage_bps: float
    fee_tier: str | None = None
    max_order_size_usd: Decimal
    min_order_size_usd: Decimal
    rate_limit_per_second: int
    is_testnet: bool = False

class BacktestGridConfig(BaseContractModel):
    """One cell in a parameter grid sweep."""
    schema_version: Literal["v1"] = "v1"
    run_id: str                                # UUID for the full grid sweep
    cell_id: str                               # UUID for this specific param combo
    strategy_id: str
    param_grid: dict[str, float]               # {param_name: value} for this cell
    start_date: date
    end_date: date
    instruments: list[str]
    venues: list[str]
    objective_metric: str                      # "sharpe" | "calmar" | "total_return"
    created_at: datetime

class BacktestGridResult(BaseContractModel):
    """Results for a single BacktestGridConfig cell."""
    schema_version: Literal["v1"] = "v1"
    cell_id: str
    run_id: str
    sharpe: float
    calmar: float
    total_return_pct: float
    max_drawdown_pct: float
    win_rate: float
    n_trades: int
    is_best_cell: bool = False
    completed_at: datetime

class MLTrainingConfig(BaseContractModel):
    """Hyperparameter config for one ML training run."""
    schema_version: Literal["v1"] = "v1"
    run_id: str
    model_type: str                            # "lightgbm" | "xgboost" | "lstm"
    hyperparams: dict[str, float]
    feature_set: list[str]
    training_start: date
    training_end: date
    validation_start: date
    validation_end: date
    target: str                                # "returns_1h" | "direction_30m"
    created_at: datetime

class MLTrainingResult(BaseContractModel):
    """Metrics output from one MLTrainingConfig run."""
    schema_version: Literal["v1"] = "v1"
    run_id: str
    val_loss: float
    val_accuracy: float | None = None
    sharpe: float
    calmar: float | None = None
    feature_importance: dict[str, float]       # feature_name → importance score
    best_epoch: int | None = None
    completed_at: datetime
```

### Config promotion workflow

```
BacktestGridResult (best cell, is_best_cell=True)
    → BacktestGridConfig.param_grid (look up cell_id)
        → StrategyConfig.signal_params (copy param_grid)
            → ConfigStore.write(strategy_id, StrategyConfig, bump config_version)
                → execution-services reads StrategyConfig on startup/hot-reload
```

### Files to create/update

- `unified-internal-contracts/unified_internal_contracts/configs/__init__.py`
- `unified-internal-contracts/unified_internal_contracts/configs/strategy.py`
- `unified-internal-contracts/unified_internal_contracts/configs/execution.py`
- `unified-internal-contracts/unified_internal_contracts/configs/backtest.py`
- `unified-internal-contracts/unified_internal_contracts/configs/ml_training.py`
- Update `unified-internal-contracts/unified_internal_contracts/__init__.py` — add all new exports to `__all__`
- Update `execution-services/execution_services/api/manual_instruction_api.py` — consume `StrategyConfig`
- Update `ml-training-service` — consume `MLTrainingConfig` and store `MLTrainingResult`

---

## Part 2 — Client Reporting System

### Current state (mr_report — /Users/ikennaigboaka/Documents/repos/other_repos/mr_report/)

Confirmed contents:
- `build_report.py` — reads `data.csv`, generates matplotlib charts (base64 embedded), renders via Jinja2 template
- `odum_mr_executive_summary_html_css_template_gold_black.html` — gold (`#D0A94A`) / black themed executive summary template
- `create_invoice_tracker.py` — dual HWM fee engine (trader HWM=10%, odum HWM per client %)
- `calculate_annual_returns.py` — compounding return calculations
- `compare_strategies.py`, `comprehensive_comparison.py` — strategy analysis
- `january_report_btc_yoav.html`, `november_report_btc_yoav.html` — BTC investor note templates (blue theme `#1d4ed8`)
- Excel tracker: 5 sheets (At-HWM, Underwater, Transaction History, Client Master List, IK Pooled)

### Three reporting tranches (confirmed from mr_report)

```
Tranche A: Fund-of-fund BTC investors
    Clients: YOAV, GUY_ASRAF
    Data source: manual CSV upload
    Template: btc_investor_note (blue theme, from january/november HTML files)
    Fee: Odum fee only (no trader fee)
    Report type: Monthly investor note

Tranche B: MENA managed accounts
    Clients: PR, NN, ET, STD, GP, SL, SL2, ANU, IK
    Data source: Secret Manager → exchange API read
    Secret name pattern: exec-{client_id}-{venue}-{account_type}
    Template: odum_executive_summary (gold/black theme)
    Fee: Odum fee + Trader fee + Introducer fee (where applicable)
    At-HWM: PR ($326,380), NN ($108,400), ET ($519,000), STD ($514,800)
    Underwater: GP, SL, SL2, ANU, IK — accrue $50/month server costs
    Server cost: $50/month per underwater account (accrues to trader)

Tranche C: Own strategies (Odum internal)
    Data source: position-balance-monitor-service + pnl-attribution-service
    Template: internal attribution report
    Fee: Internal tracking only
```

### Dual HWM Fee Engine (from mr_report reverse-engineered)

```python
# client_reporting_service/core/fee_calculator.py

class FeeCalculator:
    """Dual HWM fee engine migrated from mr_report/create_invoice_tracker.py"""

    def calculate_period_fees(
        self,
        client_id: str,
        opening_aum: Decimal,
        closing_aum: Decimal,
        trader_hwm: Decimal,
        odum_hwm: Decimal,
        fee_structure: FeeStructure,
        is_underwater: bool,
        server_cost_usd: Decimal = Decimal("50"),
    ) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """Returns (trader_fee, odum_fee, introducer_fee, server_cost)."""
        pnl = closing_aum - opening_aum

        # Trader fee: 10% of PnL above trader HWM
        pnl_above_trader_hwm = max(Decimal("0"), closing_aum - trader_hwm)
        trader_fee = pnl_above_trader_hwm * Decimal(str(fee_structure.trader_fee_pct))

        # Odum fee: client % of PnL above odum HWM
        pnl_above_odum_hwm = max(Decimal("0"), closing_aum - odum_hwm)
        odum_fee = pnl_above_odum_hwm * Decimal(str(fee_structure.odum_fee_pct))

        # Introducer fee: % of ALL HISTORICAL odum collections (not just this period)
        # NOTE: introducer_fee is calculated by reporting service on cumulative basis
        # For monthly invoice: store cumulative odum_collected in client record
        introducer_fee = Decimal("0")
        if fee_structure.introducer_fee_pct and fee_structure.introducer_id:
            introducer_fee = odum_fee * Decimal(str(fee_structure.introducer_fee_pct))

        # Server costs: $50/month if underwater, else $0
        server_cost = server_cost_usd if is_underwater else Decimal("0")

        return trader_fee, odum_fee, introducer_fee, server_cost
```

### New UIC reporting schemas: `unified_internal_contracts/reporting/`

```python
class FeeStructure(BaseContractModel):
    schema_version: Literal["v1"] = "v1"
    client_id: str
    odum_fee_pct: float
    trader_fee_pct: float
    introducer_id: str | None = None
    introducer_fee_pct: float | None = None

class HighWaterMark(BaseContractModel):
    schema_version: Literal["v1"] = "v1"
    client_id: str
    hwm_type: str                    # "odum" | "trader"
    currency: str                    # "USDT" | "BTC"
    value: Decimal
    set_at: datetime
    set_by: str                      # Google OAuth email

class ClientPerformanceRecord(BaseContractModel):
    schema_version: Literal["v1"] = "v1"
    client_id: str
    tranche: str                     # "fund_of_fund" | "managed" | "own"
    period_month: str                # "2026-01"
    opening_aum: Decimal
    closing_aum: Decimal
    currency: str
    pnl: Decimal
    return_pct: float
    trader_hwm: Decimal
    odum_hwm: Decimal
    pnl_above_odum_hwm: Decimal
    trader_fee_due: Decimal
    odum_fee_due: Decimal
    introducer_fee_due: Decimal
    server_costs: Decimal = Decimal("0")
    data_source: str                 # "api_live" | "api_static" | "manual"
    generated_at: datetime

class ClientInvoice(BaseContractModel):
    schema_version: Literal["v1"] = "v1"
    invoice_id: str                  # {client_id}-{period_month}-{uuid4_short}
    client_id: str
    period_month: str
    odum_fee_due: Decimal
    introducer_fee_due: Decimal
    server_costs: Decimal
    total_due: Decimal
    currency: str
    payment_address: str | None = Field(default=None, json_schema_extra={"pii": True})
    payment_tx_hash: str | None = None
    status: str                      # "pending" | "paid" | "waived"
    created_at: datetime

class MonthlyReport(BaseContractModel):
    schema_version: Literal["v1"] = "v1"
    report_id: str
    client_id: str
    period_month: str
    tranche: str
    report_gcs_path: str             # gs://odum-reports/{client_id}/{period_month}.html
    performance: ClientPerformanceRecord
    invoice: ClientInvoice | None = None
    ai_summary: str | None = None    # Claude-generated executive narrative
    generated_at: datetime
```

### client-reporting-service: NEW standalone repo

**Repo**: `IggyIkenna/client-reporting-service`

Setup follows `new-repo-setup.mdc` exactly:
```bash
gh repo create IggyIkenna/client-reporting-service --private --clone
gh api /repos/IggyIkenna/client-reporting-service/collaborators/CosmicTrader -f permission='push'
gh api /repos/IggyIkenna/client-reporting-service/collaborators/datado -f permission='push'
```

Structure:
```
client-reporting-service/
├── client_reporting_service/
│   ├── __init__.py
│   ├── config.py                   # extends UnifiedCloudConfig
│   ├── main.py                     # asyncio entrypoint
│   ├── api/
│   │   ├── main.py                 # FastAPI app + Google OAuth middleware
│   │   ├── routes/
│   │   │   ├── reports.py          # GET /reports/{client_id}, GET /reports/{id}/html
│   │   │   ├── invoices.py         # GET /invoices/{client_id}/pending, PATCH mark-paid
│   │   │   ├── hwm.py              # GET/POST /clients/{id}/hwm
│   │   │   └── generate.py         # POST /reports/generate, POST /reports/upload-tranche-a
│   ├── core/
│   │   ├── fee_calculator.py       # FeeCalculator — migrated from mr_report
│   │   ├── report_generator.py     # Jinja2 HTML generation, matplotlib charts
│   │   ├── tranche_router.py       # routes A/B/C data sources
│   │   └── ai_summary.py           # Claude API executive summary
│   └── templates/
│       ├── odum_executive_summary.html   # gold/black template from mr_report
│       └── btc_investor_note.html        # blue theme from mr_report
├── tests/
├── pyproject.toml
├── Dockerfile
└── scripts/quality-gates.sh
```

pyproject.toml key deps:
```toml
dependencies = [
    "fastapi>=0.109.0,<1.0.0",
    "uvicorn[standard]>=0.27.0,<1.0.0",
    "unified-internal-contracts>=1.0.0,<2.0.0",
    "unified-trading-services>=2.2.0,<3.0.0",
    "unified-config-interface>=1.2.0,<2.0.0",
    "unified-events-interface>=2.0.0,<3.0.0",
    "unified-cloud-interface>=1.0.0,<2.0.0",
    "jinja2>=3.0.0,<4.0.0",
    "matplotlib>=3.9.0,<4.0.0",
    "anthropic>=0.40.0,<1.0.0",
    "google-auth>=2.40.0,<3.0.0",
    "pyyaml>=6.0.0,<7.0.0",
]
```

### Report generation pipeline

```
POST /reports/generate {client_id, period_month}
    ↓ tranche_router.get_data_source(client_id)   ← reads credentials-registry.yaml
    ↓ Tranche A → accept manual CSV data
    ↓ Tranche B → get_secret(exec-{client_id}-{venue}-{account_type})
                 → query exchange API → closing_aum, fills for period
    ↓ Tranche C → GET position-balance-monitor-service /positions
                + GET pnl-attribution-service /pnl/{client_id}
    ↓ FeeCalculator.calculate_period_fees(...)
    ↓ ClientPerformanceRecord constructed
    ↓ ClientInvoice generated (if managed tranche)
    ↓ report_generator.render_html(performance, invoice, template)
        ↓ matplotlib charts (monthly_returns bar chart, cumulative equity curve)
        ↓ embed charts as base64 data URIs
        ↓ Jinja2 render → self-contained HTML
    ↓ ai_summary.generate(performance) → anthropic claude-3-5-haiku
    ↓ get_storage_client().upload(gs://odum-reports/{client_id}/{period}.html)
    ↓ MonthlyReport stored as JSON sidecar at gs://odum-reports/{client_id}/{period}.json
    ↓ FCA retention: GCS lifecycle policy 5 years
```

### API Endpoints

```
GET  /health                                        → health check
GET  /reports/{client_id}                           → list[MonthlyReport] (CLIENT: own only)
GET  /reports/{client_id}/{period_month}            → MonthlyReport
POST /reports/generate                              → trigger generation (ADMIN)
GET  /reports/{report_id}/html                      → serve HTML from GCS
POST /reports/upload-tranche-a                      → Tranche A CSV upload (ADMIN)
GET  /invoices/{client_id}/pending                  → list unpaid ClientInvoice
PATCH /invoices/{invoice_id}/mark-paid              → record tx_hash (COMPLIANCE)
GET  /clients/{client_id}/hwm                       → current HighWaterMark
POST /clients/{client_id}/hwm                       → set HighWaterMark (ADMIN)
GET  /metrics                                       → Prometheus metrics endpoint
```

---

## Part 3 — Auth: Google OAuth Everywhere

### Decision

Replace Okta (`@okta/okta-auth-js`) with Google OAuth across all UIs. Rationale: easier to set up, native to GCP stack, can migrate to Okta SSO later.

### Frontend (all UIs)

```typescript
// src/auth/GoogleAuth.tsx
// Uses Google OAuth2 implicit flow
// Redirects to https://accounts.google.com/o/oauth2/v2/auth
// Stores id_token in sessionStorage (NOT localStorage)
// Attaches Bearer token to all API calls via axios interceptor

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID
const SKIP_AUTH = import.meta.env.VITE_SKIP_AUTH === 'true'
// Local dev: VITE_SKIP_AUTH=true bypasses auth entirely
```

```typescript
// src/auth/RequireAuth.tsx
// Checks sessionStorage for valid non-expired id_token
// Redirects to /login if missing/expired
// Checks role claim against required minimum role
```

### Backend (all FastAPI services)

```python
# unified_trading_services/auth/google_oauth.py
# GoogleOAuthMiddleware: verifies Bearer token, extracts sub/email/groups
# get_current_user() FastAPI dependency
# role_required("ADMIN") / role_required("COMPLIANCE") etc.
# GOOGLE_OAUTH_DOMAIN env: restrict to @odum-research.com
# Local dev: GOOGLE_OAUTH_DOMAIN="" skips domain check
```

### RBAC Roles (Google Groups)

```
ADMIN       → all UIs + config write + report generation
TRADER      → live-health-monitor-ui (read + manual trade), trading-analytics-ui
ANALYST     → backtest-ui (read), logs-dashboard-ui, batch-audit-ui, ml-deployment-ui
CLIENT      → client-reporting-ui (own reports only, filtered by sub claim = client_id)
COMPLIANCE  → settlement-ui, audit logs, invoice mark-paid
```

---

## Part 4 — UI Restructuring

### Confirmed UI inventory and actions

| UI | Current State | Auth | Action |
|----|--------------|------|--------|
| `live-health-monitor-ui` | 4 real pages (recharts, no auth) | Add Google OAuth TRADER | Add RequireAuth, add SSE |
| `onboarding-ui` | 6 pages (all TODO stubs, axios JWT stub) | Add Google OAuth ADMIN | Wire all pages to backends |
| `settlement-ui` | Has duplicate ManualTradingPanel | Add Google OAuth COMPLIANCE | Remove ManualTrading, repurpose |
| `client-reporting-ui` | Shell (Okta stub) | Replace → Google OAuth CLIENT | Build all pages |
| `backtest-ui` | Shell (Okta stub) | Replace → Google OAuth ANALYST | Build all pages |
| `trading-analytics-ui` | Shell (Okta stub + VITE_SKIP_AUTH) | Replace → Google OAuth TRADER | Build all pages |
| `ml-deployment-ui` | Shell (Okta conditional) | Replace → Google OAuth ANALYST | Build as ML Analytics UI |
| `batch-audit-ui` | Shell | Add Google OAuth ANALYST | Build minimal viable |
| `logs-dashboard-ui` | Shell | Add Google OAuth ANALYST | Wire SSE logs |
| `strategy-ui` | **DOES NOT EXIST** | Google OAuth ANALYST | Create new repo |

### settlement-ui pages (after repurpose)

```
/positions          → EOD position snapshot (position-balance-monitor-service GET /positions)
/reconciliation     → drift table (GET /reconciliation/status + POST /reconciliation/trigger)
/invoices           → ClientInvoice table (client-reporting-service GET /invoices/{id}/pending)
/reports            → MonthlyReport browser (client-reporting-service GET /reports/{id})
/hwm                → HighWaterMark history (GET /clients/{id}/hwm)
```

### SSE endpoints to add

| Service | Endpoint | Data |
|---------|----------|------|
| execution-results-api | `GET /stream/fills` | FillEventPubSubPayload |
| position-balance-monitor-service | `GET /stream/positions` | PositionResponse delta |
| alerting-system | `GET /stream/alerts` | AlertEvent (for live-health-monitor-ui) |

SSE library: `sse-starlette>=1.6.1` added to pyproject.toml of each service.

---

## Part 5 — Manual Trading Consolidation

**Single source of truth**: `live-health-monitor-ui` only.

Remove from `settlement-ui` (done in settlement-ui-repurpose todo).

API gaps in `execution-services/execution_services/api/manual_instruction_api.py`:

```python
# Add these endpoints:
POST /manual/cancel   body: {instruction_id: str, reason: str}
POST /manual/amend    body: {instruction_id: str, new_quantity: Decimal, new_price: Decimal | None, reason: str}
# Both validate against ManualInstruction UIC schema
# Both require submitted_by from Google OAuth token
# Both log via log_event() from unified-events-interface
```

UI additions to `live-health-monitor-ui/src/components/ManualTradingPanel.tsx`:
- `submitted_by` field (read from sessionStorage OAuth token, non-editable display)
- `reason` textarea (required, min 10 chars)
- Cancel button per pending instruction
- Amend form per pending instruction

---

## Part 6 — Onboarding UI Completeness

All pages in onboarding-ui currently have `{/* TODO: Implement */}` stubs. Full implementation required.

Backend needed: onboarding-service (or extend an existing service). Given onboarding is ADMIN-only, extend `client-reporting-service` to add `/onboarding/*` routes rather than creating a fourth new service.

New routes in client-reporting-service:
```
POST /onboarding/clients/{id}/aml-screen        body: {wallet_address}
POST /onboarding/clients/{id}/fee-structure     body: FeeStructure
POST /onboarding/clients/{id}/hwm               body: HighWaterMark
POST /onboarding/clients/{id}/api-key           body: {venue, api_key_encrypted, api_secret_encrypted}
GET  /onboarding/clients/{id}/status            → ClientOnboardingStatus
GET  /audit/events?entity_id={id}&limit=100     → list[AuditLogEntry]
```

AuditLogEntry stored in GCS `gs://odum-audit/{entity_id}/{timestamp}.json` (FCA 5-year retention).

---

## Part 7 — New Repos Required

| Repo | Type | Purpose |
|------|------|---------|
| `client-reporting-service` | Python FastAPI service | Report generation, fee engine, invoice management |
| `strategy-ui` | React UI | Strategy config viewer, backtest trigger, live status |
| `market-data-api` | Python FastAPI service | Order book SSE endpoint (see monitoring plan) |

Each new repo follows `new-repo-setup.mdc` workflow exactly:
1. `gh repo create IggyIkenna/{name} --private --clone`
2. Grant CosmicTrader + datado push access
3. Scaffold with quality-gates.sh
4. `uv lock && uv pip install -e {name}/` from workspace root
5. Update workspace-manifest.json
6. `bash scripts/quickmerge.sh "feat: initial scaffold"`

---

## Summary: All Todos (Execution Order)

**Wave 1 — Foundations (blocking everything)**:
1. `reportany-error-all-repos` — must be clean before adding new code
2. `credentials-registry-create`
3. `config-schemas-uic`
4. `reporting-schemas-uic`
5. `client-onboarding-schema`
6. `manual-instruction-schema`

**Wave 2 — Backend Services**:
7. `google-oauth-shared-middleware`
8. `client-reporting-service-new-repo`
9. `mr-report-migration`
10. `reporting-backend-api`
11. `three-tranche-data-wiring`
12. `ai-report-summaries`
13. `service-ui-separation-audit`
14. `sse-endpoints-add`
15. `config-promotion-workflow`
16. `ml-training-config-wire`

**Wave 3 — UIs**:
17. `auth-rbac-all-uis`
18. `client-reporting-ui-build`
19. `settlement-ui-repurpose`
20. `backtest-ui-build`
21. `trading-analytics-ui-build`
22. `manual-trading-consolidate`
23. `onboarding-ui-gaps`
24. `ml-deployment-ui-scope-correct`
25. `strategy-ui-new-repo`
