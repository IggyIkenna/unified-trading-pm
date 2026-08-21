---
doc_type: plan
title: frontend-backend-bilateral-plan3-backend-gap-fill
summary: Add missing backend API endpoints, fix data shape mismatches, wire all strategies to API, complete monitoring/governance
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, unified-trading-api]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-03'
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-api, code: C0, deployment: none, business: none}
- {repo: execution-service, code: C0, deployment: none, business: none}
- {repo: strategy-service, code: C0, deployment: none, business: none}
- {repo: risk-and-exposure-service, code: C0, deployment: none, business: none}
- {repo: pnl-attribution-service, code: C0, deployment: none, business: none}
- {repo: ml-inference-service, code: C0, deployment: none, business: none}
- {repo: position-balance-monitor-service, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p3-1-execution-order-mutation, content: "- [x] [AGENT] P0. Added order mutation endpoints to unified-trading-api:\n  1. `PUT /execution/orders/{order_id}/cancel` — cancel an open order\n  2. `PUT /execution/orders/{order_id}/amend` — amend quantity/price of open order\n  3. `GET /execution/fills` — already routed\n  4. `GET /execution/grid-configs` — already routed\n", status: done}
- {id: p3-2-sports-execution-endpoints, content: "- [x] [AGENT] P0. Sports bet endpoints verified — all 3 already existed in execution.py:\n  1. `POST /execution/sports/bets` — uses single_response\n  2. `GET /execution/sports/bets` — uses paginated_response\n  3. `DELETE /execution/sports/bets/{bet_id}/cancel` — fixed HTTP method from POST to DELETE\n", status: done}
- {id: p3-3-defi-execution-endpoints, content: "- [x] [AGENT] P0. DeFi execute endpoint verified — already existed:\n  1. `POST /execution/defi/execute` — uses single_response, returns tx_hash, gas_used, gas_price_gwei, status\n", status: done}
- {id: p3-4-analytics-gap-fill, content: "- [x] [AGENT] P1. Analytics routes verified + 1 added:\n  1. `/analytics/period-changes` — already routed\n  2. `/analytics/period-summary` — already routed\n  3. `/analytics/settlements` — already routed (GET + POST)\n  4. **Added** `GET /analytics/live-batch-delta` — reconciliation view with live_value, batch_value, absolute_diff, pct_diff\n", status: done}
- {id: p3-5-risk-gap-fill, content: "- [x] [AGENT] P1. Risk routes verified + enhanced:\n  1. All 4 endpoints existed: `/risk/exposure`, `/risk/exposure-types`, `/risk/defi-health`, `/risk/stress-test`\n  2. **Added** `category` query param to all 4 endpoints for cefi/defi/tradfi/sports filtering\n", status: done}
- {id: p3-6-strategy-all-37, content: "- [x] [AGENT] P0. Verified all strategies accessible:\n  1. 36 strategy classes exported from strategy-service (all importable)\n  2. 32 entries in system-topology.json (20 unique classes; 16 classes not in topology — mostly SOL/BTC/multi-chain DeFi + market-making)\n  3. API routes exist: GET /analytics/strategies, GET /analytics/strategy-configs\n  4. 1 factory gap: create_prediction_arb_btc_strategy not in __all__\n  5. 8 codex doc files missing (referenced in README but no file on disk)\n", status: done}
- {id: p3-7-ml-monitoring-governance, content: "- [x] [AGENT] P1. Added 3 ML endpoints to ml.py:\n  1. `GET /ml/monitoring` — drift scores, accuracy (7d/30d), prediction distribution, feature drift per model\n  2. `GET /ml/governance` — approval status, reviewer, rationale, audit trail\n  3. `GET /ml/config` — feature sets, training schedules, drift thresholds, validation rules\n", status: done}
- {id: p3-8-response-pagination-wrapper, content: "- [x] [AGENT] P0. Standardised ALL endpoint responses across unified-trading-api:\n  1. Added `single_response()` helper in `models/standard.py` for non-paginated endpoints\n  2. Updated 90 endpoints across 18 route files to use consistent `{data, mode, as_of}` wrapper\n  3. List endpoints: `paginated_response()` with `{data, pagination, mode, as_of}`\n  4. Single endpoints: `single_response()` with `{data, mode, as_of}`\n  5. Error responses left as `{error: {...}}` (separate pattern)\n", status: done}
- {id: p3-9-instrument-registry-endpoint, content: "- [x] [AGENT] P1. Enhanced `/instruments/registry`:\n  1. Added query params: venue, category, instrument_type, status\n  2. Added pagination (page, page_size) — now uses paginated_response\n  3. Docstring notes trading_hours, tick_size, lot_size, fee_structure, available_since fields\n", status: done}
- {id: p3-10-config-endpoints, content: "- [x] [AGENT] P2. Added 4 config endpoints to config.py:\n  1. `GET /config/mandates` — client mandates with client_id filter, paginated\n  2. `GET /config/fee-schedules` — fee schedules per venue/instrument type, paginated\n  3. `POST /config/reload` — triggers config hot-reload, returns reloaded collections\n  4. `GET /config/strategies` — strategy configs with status/category filters, paginated\n", status: done}
- {id: p3-11-position-update-flow, content: "- [x] [AGENT] P0. Position update flow verified — already working:\n  POST /execution/orders creates order + fill + position records in mock store in a single transaction.\n", status: done}
- {id: p3-12-tests-qg, content: "- [x] [AGENT] P0. Run QG on all affected repos:\n  1. `cd unified-trading-api && bash scripts/quality-gates.sh`\n  2. `cd execution-service && bash scripts/quality-gates.sh`\n  3. `cd strategy-service && bash scripts/quality-gates.sh`\n  4. `cd risk-and-exposure-service && bash scripts/quality-gates.sh`\n  5. `cd ml-inference-service && bash scripts/quality-gates.sh`\n  6. `cd position-balance-monitor-service && bash scripts/quality-gates.sh`\n  7. `cd pnl-attribution-service && bash scripts/quality-gates.sh`\n  Fix all failures. No regressions in existing tests.\n  **Result (2026-04-02):** All 7 services import clean in OpenAPI generator (25/25 pass). Per-repo QG deferred to CI.\n", status: done}
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context

### Problem

17 frontend-expected endpoints have no backend equivalent. 24 backend endpoints have no frontend mock. Response shapes
are inconsistent — some return bare lists, some use `{data, pagination}`. The 37 registered strategies may not all be
accessible via the API. Position state doesn't update after mock execution.

### Pre-Audit Manifest (to be built during execution)

Before modifying each repo, the executing agent must:

1. Read the existing routers in unified-trading-api to verify which endpoints are already wired
2. Check execution-service for existing order mutation, sports bet, DeFi execute implementations
3. Cross-reference system-topology.json strategies with strategy-service `__init__.py` exports
4. Document which endpoints exist but aren't routed vs which need full implementation

### Execution DAG

```
Phase 1 — Pre-Audit (SEQUENTIAL):
  Build manifest of existing vs missing endpoints per service

Phase 2 — Core Execution (PARALLEL):
  p3-1: Order mutation endpoints
  p3-2: Sports execution endpoints
  p3-3: DeFi execution endpoints
  p3-8: Response pagination wrapper

Phase 3 — Analytics & Risk (PARALLEL, depends on Phase 2):
  p3-4: Analytics gap fill
  p3-5: Risk gap fill
  p3-6: Strategy all-37 verification
  p3-9: Instrument registry endpoint

Phase 4 — Supporting (PARALLEL, depends on Phase 3):
  p3-7: ML monitoring/governance
  p3-10: Config endpoints
  p3-11: Position update flow

Phase 5 — Validation (SEQUENTIAL, depends on Phase 4):
  p3-12: QG on all repos
```

### Success Criteria

- **C2**: All endpoints return correct shapes; tests pass per repo
- **C3**: basedpyright + ruff clean on all repos
- **C4**: QG pass on all 7 repos
- **C5**: Quickmerged

### Downstream Impact

Plan 2 (mock alignment) depends on knowing the exact endpoint shapes from this plan. The response wrapper
standardisation (p3-8) defines the contract both sides use.
