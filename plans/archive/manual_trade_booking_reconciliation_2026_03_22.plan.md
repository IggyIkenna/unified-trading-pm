---
doc_type: plan
title: manual-trade-booking-reconciliation
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [batch-live-reconciliation-service, deployment-service, execution-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-22'
remaining_todos_consolidated_into: consolidated_operational_validation_2026_04_15
superseded_by: [consolidated_operational_validation_2026_04_15.plan.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview: Citadel-grade manual trade booking across all instrument types (CeFi, DeFi, TradFi, Sports, Prediction) with two UI surfaces (back-office + in-context), record-only fills for OTC/missed trades, reconciliation accept/reject workflow, dual execution-service deployment (LIVE + MANUAL instances), and OperationalMode schema validation.
type: mixed
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-03-22
completion_gates: {code: C5, deployment: D2, business: none}
repo_gates:
- {repo: unified-api-contracts (internal), code: C4, deployment: none, business: none}
- {repo: execution-service, code: C3, deployment: none, business: none}
- {repo: batch-live-reconciliation-service, code: C1, deployment: none, business: none}
- {repo: deployment-service, code: C1, deployment: none, business: none}
- {repo: unified-trading-system-ui, code: C3, deployment: none, business: none}
- {repo: unified-trading-pm (codex/ subdir), code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p1a-operational-mode-enum, content: "- [x] [AGENT] P0. Add `OperationalMode` StrEnum to `unified-api-contracts (internal)/unified_internal_contracts/modes.py`.\n  Values: LIVE=\"live\", MANUAL=\"manual\", BACKTEST=\"backtest\", PAPER=\"paper\".\n  Docstring: \"Per-service operational mode — validated at startup. Injected as OPERATIONAL_MODE env var.\"\n  Add to `__all__` in modes.py.\n  Add `from unified_internal_contracts.modes import OperationalMode` to `__init__.py` line ~425 (after existing modes imports).\n  Add `\"OperationalMode\"` to `__all__` in `__init__.py` (alphabetical order, ~880).\n", status: done, note: Existing `ExecutionMode` in execution_preferences.py is AGGRESSIVE/PASSIVE/NEUTRAL/TWAP/VWAP — different concept.}
- {id: p1b-manual-execution-mode-enum, content: "- [x] [AGENT] P0. Add `ManualExecutionMode` StrEnum to `unified-api-contracts (internal)/unified_internal_contracts/execution.py`.\n  Values: EXECUTE=\"execute\" (route to venue via orchestrator), RECORD_ONLY=\"record_only\" (skip venue, record fill directly — OTC, missed, simulation).\n  CANNOT be named `ExecutionMode` — that already exists in `domain/execution_service/execution_preferences.py` (AGGRESSIVE/PASSIVE/etc).\n  Add to `__all__` in execution.py.\n  Add import + `\"ManualExecutionMode\"` to `__init__.py`.\n", status: done, note: ''}
- {id: p1c-extend-manual-instruction, content: "- [x] [AGENT] P0. Extend `ManualInstruction` in `unified-api-contracts (internal)/unified_internal_contracts/execution.py`.\n  Add fields (all with defaults so existing consumers don't break):\n  - `execution_mode: ManualExecutionMode = ManualExecutionMode.EXECUTE`\n  - `client_id: str = \"\"`  (org hierarchy)\n  - `strategy_id: str = \"\"`  (org hierarchy)\n  - `portfolio_id: str = \"\"`  (org hierarchy — book)\n  - `category: str = \"\"`  (DeploymentCluster value or instrument category)\n  - `counterparty: str = \"\"`  (OTC counterparty identifier)\n  - `source_reference: str = \"\"`  (external trade ID / exchange reference)\n  Update docstring to document new fields. Update existing `submitted_by` docstring: \"Identity of the operator (OAuth sub claim).\"\n", status: done, note: 'Existing ManualInstruction has: instruction_id, submitted_by, venue, account_id, instrument_key, side, order_type, quantity, submitted_at, price, reason'}
- {id: p1d-reconciliation-schema, content: "- [x] [AGENT] P0. Create `unified-api-contracts (internal)/unified_internal_contracts/reconciliation.py`.\n  Add `ReconciliationAction` StrEnum: ACCEPT=\"accept\", REJECT=\"reject\", INVESTIGATE=\"investigate\".\n  Add `ReconciliationResolution` BaseModel:\n  - break_id: str\n  - action: ReconciliationAction\n  - note: str = Field(min_length=10)  # FCA audit trail\n  - resolved_by: str  # OAuth sub\n  - correcting_instruction_id: str | None = None  # Links to manual booking when action=REJECT\n  Add `__all__` to file. Add imports + exports to `__init__.py`.\n", status: done, note: batch-live-reconciliation-service already has ReconStatus/DeviationRecord in its own models/ — those are service-internal. This is cross-service contract.}
- {id: p1e-delete-duplicate-manual-instruction, content: "- [x] [AGENT] P0. Delete `unified-api-contracts (internal)/unified_internal_contracts/domain/execution_service/manual_instruction.py`.\n  This is a byte-for-byte duplicate of ManualInstruction in execution.py. Root `__init__.py` already imports from execution.py (line 352). `domain/execution_service/__init__.py` does NOT export it.\n  Verify no imports reference the domain path: `rg \"from.*domain.execution_service.manual_instruction\" --type py`\n  Delete the file. Run `cd unified-api-contracts && bash scripts/quality-gates.sh` to confirm no breakage.\n", status: done, note: ''}
- {id: p1f-uic-quality-gate, content: "- [x] [AGENT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh`.\n  All new symbols importable: OperationalMode, ManualExecutionMode, ReconciliationAction, ReconciliationResolution.\n  basedpyright clean. ruff clean. All existing tests pass. No regressions.\n", status: done, note: QG GATE — Phase 2 blocked until this passes.}
- {id: p2a-validate-operational-mode, content: "- [x] [AGENT] P0. In `execution-service/execution_service/cli/handlers/__init__.py`, update `get_handler_for_operation()`:\n  Import `OperationalMode` from UIC. Validate `operation` param against `OperationalMode` enum values.\n  If operation not in OperationalMode → raise ValueError with message listing valid values.\n  Existing mapping: \"backtest\"→BacktestHandler, \"live_execution\"/\"execute\"/\"manual\"→LiveExecutionHandler.\n  Map \"paper\" → LiveExecutionHandler with paper flag (or raise NotImplementedError for now).\n", status: done, blocked_by: p1f-uic-quality-gate, note: ''}
- {id: p2b-extend-manual-request-schema, content: "- [x] [AGENT] P0. In `execution-service/execution_service/api/manual_schemas.py`, add fields to `ManualInstructionRequest`:\n  - `execution_mode: str = Field(default=\"execute\", description=\"execute or record_only\")`\n  - `portfolio_id: str = Field(default=\"\", description=\"Portfolio/book identifier\")`\n  - `category: str = Field(default=\"\", description=\"Instrument category\")`\n  - `counterparty: str = Field(default=\"\", description=\"OTC counterparty\")`\n  - `source_reference: str = Field(default=\"\", description=\"External trade ID\")`\n  Add `RecordOnlyFillResponse(BaseModel)`: fill_id, instruction_id, status, message.\n  Update Config.json_schema_extra example to include new fields.\n", status: done, blocked_by: p1f-uic-quality-gate, note: client_id already exists on ManualInstructionRequest.}
- {id: p2c-record-only-mode, content: "- [x] [AGENT] P0. In `execution-service/execution_service/api/manual_instruction_api.py`, add record-only branch:\n  After validation in `submit_manual_instruction()`, check `request.execution_mode == \"record_only\"`.\n  If record-only:\n  1. Skip venue validation (OTC has no venue constraint)\n  2. Build CanonicalFill (from UAC) with: fill_id=UUID, order_id=instruction_id, timestamp=now(UTC), venue=request.venue, instrument_id=request.instrument_id, side=OrderSide(request.side.lower()), price=request.price or Decimal(\"0\"), quantity=request.quantity, strategy_id=request.strategy_id, client_id=request.client_id\n  3. Publish to Pub/Sub `fill-events-manual` topic via `get_pubsub_client()` from UCI\n  4. Log `MANUAL_FILL_RECORDED` event via log_event()\n  5. Persist audit log with ManualInstruction (execution_mode=RECORD_ONLY)\n  6. Return ManualInstructionResponse with status=\"RECORDED\"\n  If execute: existing orchestrator flow unchanged.\n  Create\
    \ helper `_record_fill_directly(request, instruction_id) -> ManualInstructionResponse`.\n", status: done, blocked_by: p2b-extend-manual-request-schema, note: 'Import CanonicalFill from unified_api_contracts.execution, get_pubsub_client from unified_cloud_interface.'}
- {id: p2d-dynamic-venue-list, content: "- [x] [AGENT] P0. In `execution-service/execution_service/api/manual_instruction_api.py`:\n  Replace hardcoded `_SUPPORTED_VENUES = [\"binance\", \"coinbase\", \"deribit\", \"bybit\"]` (line 90) with dynamic lookup:\n  `from unified_api_contracts.registry import CAPABILITY_DECLARATIONS`\n  Create `_get_supported_venues() -> set[str]` that returns venues with trading capability from registry.\n  Use `@lru_cache` for performance.\n  In `_validate_instruction_request()`, skip venue check when execution_mode is record_only.\n", status: done, blocked_by: p1f-uic-quality-gate, note: CAPABILITY_DECLARATIONS is the SSOT for all venue capabilities.}
- {id: p2e-algos-venues-endpoints, content: "- [x] [AGENT] P1. Add two new GET endpoints to `execution-service/execution_service/api/manual_instruction_api.py`:\n  1. `GET /manual/venues` → returns `{\"venues\": [\"binance\", \"deribit\", ...]}` from `_get_supported_venues()`\n  2. `GET /manual/algos` → returns `{\"algos\": {\"default\": [\"MARKET\",\"TWAP\",\"VWAP\",\"ICEBERG\",\"SOR\",\"BEST_PRICE\",\"BENCHMARK_FILL\"]}}` (per-venue algo lists can be refined later)\n  These serve the `useVenues()` and `useAlgos()` hooks already in the UI.\n", status: done, blocked_by: p2d-dynamic-venue-list, note: ''}
- {id: p2f-execution-service-quality-gate, content: "- [x] [AGENT] P0. Run `cd execution-service && bash scripts/quality-gates.sh`.\n  basedpyright clean. ruff clean. All tests pass including test_manual_operation.py. No regressions.\n", status: todo, note: QG GATE — Phase 3 blocked until this passes.}
- {id: p3a-recon-resolution-api, content: "- [x] [AGENT] P1. Create `batch-live-reconciliation-service/batch_live_reconciliation_service/api/resolution_api.py`.\n  Add FastAPI router with prefix `/reconciliation`:\n  1. `POST /reconciliation/resolve` — body: ReconciliationResolution (from UIC). Persist to GCS audit log via get_storage_client(). Log `RECONCILIATION_BREAK_RESOLVED` event. Return {break_id, status, action}.\n  2. `GET /reconciliation/breaks` — query params: venue, break_type, status, from_date, to_date. Read from stage5 results in GCS (or fallback mock data). Return list of breaks.\n  3. `POST /reconciliation/book-correction` — body: {break_id}. Look up break details, return pre-filled ManualInstructionRequest dict with execution_mode=record_only, instrument, venue, delta quantity, reason referencing break_id.\n  Register router in the service's app.py / main entry point.\n", status: done, blocked_by: p2f-execution-service-quality-gate, note: 'If service has no FastAPI app
    yet, create minimal one. Check existing entry points.'}
- {id: p3b-dual-execution-cluster, content: "- [x] [AGENT] P1. Update all `deployment-service/configs/clusters/*.yaml` (cefi.yaml, defi.yaml, tradfi.yaml, sports.yaml, prediction.yaml, full.yaml):\n  Add second execution-service entry:\n  ```yaml\n  services:\n    - execution-service               # LIVE operational mode\n    - execution-service:manual         # MANUAL operational mode (operator booking + backup)\n  ```\n  The `:manual` suffix is a service instance annotation. deployment-service orchestrator passes `OPERATIONAL_MODE=manual` env var to the second instance.\n  Document the dual-instance pattern in a comment at top of each cluster YAML.\n", status: done, blocked_by: p1f-uic-quality-gate, note: 6 cluster YAML files to update.}
- {id: p3c-phase3-quality-gate, content: "- [ ] [AGENT] P0. Run QG on both repos:\n  `cd batch-live-reconciliation-service && bash scripts/quality-gates.sh`\n  `cd deployment-service && bash scripts/quality-gates.sh`\n", status: done, note: QG GATE — Phase 4 blocked until this passes.}
- {id: p4a-extend-hooks, content: "- [ ] [AGENT] P0. Extend `unified-trading-system-ui/hooks/api/use-orders.ts`:\n  Add to PlaceOrderParams interface: execution_mode?: \"execute\" | \"record_only\", counterparty?: string, source_reference?: string, category?: string, portfolio_id?: string, algo?: string, algo_params?: Record<string, string | number>.\n  Pass these through in the usePlaceOrder mutation body.\nExtend `unified-trading-system-ui/hooks/api/use-reports.ts`:\n  Add `useResolveBreak()` — useMutation for POST /api/reporting/reconciliation/resolve (body: {break_id, action, note, resolved_by}).\n  Add `useReconciliationBreaks(params)` — useQuery for GET /api/reporting/reconciliation/breaks with filter query params.\n  Add `useBookCorrection()` — useMutation for POST /api/reporting/reconciliation/book-correction (body: {break_id}).\n", status: done, blocked_by: p3c-phase3-quality-gate, note: Check existing hook patterns in use-orders.ts and use-reports.ts for mutation/query conventions.}
- {id: p4b-back-office-booking-page, content: "- [ ] [AGENT] P0. Create `unified-trading-system-ui/app/(platform)/services/trading/book/page.tsx`.\n  Full-page form (NOT sheet/drawer — this is a dedicated back-office screen):\n  1. **Hierarchy selectors** (top bar): Org→Client→Strategy cascading dropdowns from `useOrganizationsList()` + `useStrategies()`\n  2. **Execution mode toggle**: EXECUTE vs RECORD_ONLY — prominent SegmentedControl/Tabs. Changes which fields are visible.\n  3. **Category tabs**: CeFi Spot | CeFi Derivatives | DeFi Swap | DeFi Lending | DeFi LP | TradFi | Sports | Prediction. Each tab shows only relevant fields.\n  4. **Core fields** (all tabs): venue (dynamic from new `useVenues` hook → GET /manual/venues), instrument (text input + search, filtered by category/venue), side (BUY/SELL buttons), quantity, price\n  5. **EXECUTE mode**: algo dropdown (from `useAlgos`), algo params (TWAP: duration_minutes, ICEBERG: num_slices, SOR: max_slippage_bps)\n  6. **RECORD_ONLY mode**:\
    \ counterparty input, source_reference input, fill_timestamp picker, fee + fee_currency\n  7. **Pre-trade compliance** (EXECUTE only): reuse existing `usePreTradeCheck` hook with PASS/FAIL badges (same pattern as ManualTradingPanel)\n  8. **Preview + confirm**: same preview → confirm flow as ManualTradingPanel\n  9. **URL prefill**: read `searchParams.get(\"prefill\")` → JSON.parse → populate form (for recon→booking flow)\n  Use existing UI components: Select, Tabs, Input, Button, Badge, Card from @/components/ui/.\n  Wire submission to `usePlaceOrder()` with all new fields.\n", status: done, blocked_by: p4a-extend-hooks, note: 'Follow same patterns as ManualTradingPanel for styling, compliance, preview.'}
- {id: p4c-add-book-trade-nav, content: "- [ ] [AGENT] P0. Add \"Book Trade\" nav entry in `unified-trading-system-ui/components/shell/service-tabs.tsx` under the Trading section.\n  Find the Trading tabs definition, add: `{ label: \"Book Trade\", href: \"/services/trading/book\" }`.\n  Use PenLine icon from lucide-react (already imported in manual-trading-panel.tsx).\n", status: done, blocked_by: p4b-back-office-booking-page, note: ''}
- {id: p4d-phase4-quality-gate, content: "- [ ] [AGENT] P0. Run UI quality gates:\n  `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build`\n  `cd unified-trading-system-ui && CI=true npm test -- --run`\n  Build must succeed. All vitest tests must pass. No type errors.\n", status: done, note: QG GATE — Phase 5 blocked until this passes.}
- {id: p5a-enhanced-manual-trading-panel, content: "- [ ] [AGENT] P0. Enhance `unified-trading-system-ui/components/trading/manual-trading-panel.tsx`:\n  1. Replace hardcoded venue list `[\"Binance\", \"Deribit\", \"Hyperliquid\", \"Coinbase\", \"OKX\", \"Bybit\", \"Uniswap\", \"Aave\"]` (line 202) with dynamic `useVenues()` hook data. Map venue slugs to display names.\n  2. Add algo dropdown after order type tabs: MARKET (default), TWAP, VWAP, ICEBERG, SOR, BEST_PRICE, BENCHMARK_FILL. Fetch from `useAlgos()`. Only show when order type is relevant.\n  3. Add algo params section (conditional): TWAP → duration_minutes input, ICEBERG → num_slices input, SOR → max_slippage_bps input.\n  4. Add instruction_type selector (Select component): TRADE, SWAP, LEND, BORROW, STAKE — visible based on venue category.\n  5. Add subtle EXECUTE/RECORD_ONLY toggle (default EXECUTE). When RECORD_ONLY: show counterparty + source_reference inputs.\n  6. Pass all new fields through to `usePlaceOrder()` mutation.\n",
  status: done, blocked_by: p4d-phase4-quality-gate, note: 'Keep the Sheet/drawer pattern — this is the in-context panel, not the back-office page.'}
- {id: p5b-recon-accept-reject-actions, content: "- [ ] [AGENT] P0. Enhance `unified-trading-system-ui/app/(platform)/services/reports/reconciliation/page.tsx`:\n  1. Add \"Actions\" column to `historyColumns` ColumnDef array (after \"Status\" column).\n  2. For non-resolved rows: render 3 icon buttons — Accept (CheckCircle2, green), Reject (XCircle, red), Investigate (Search, blue).\n  3. Each button opens a Popover/AlertDialog with: note TextArea (min 10 chars for FCA), Confirm button.\n  4. On confirm: call `useResolveBreak()` mutation with {break_id: row.id, action, note, resolved_by: user.email}.\n  5. On success: refetch via `useReconciliationBreaks()` queryClient.invalidateQueries.\n  6. Replace `FALLBACK_HISTORY` usage: use `useReconciliationBreaks()` as primary data source, keep FALLBACK_HISTORY only when API returns empty/error.\n", status: done, blocked_by: p4d-phase4-quality-gate, note: Can run in PARALLEL with p5a.}
- {id: p5c-book-correction-flow, content: "- [ ] [AGENT] P0. Add \"Book Correction\" button to reconciliation page:\n  1. Show \"Book Correction\" button (PenLine icon) on rows with status=\"rejected\".\n  2. On click: call `useBookCorrection()` with {break_id}.\n  3. On response: navigate to `/services/trading/book?prefill=${encodeURIComponent(JSON.stringify(response))}`.\n  4. The back-office page (Phase 4) reads this param and pre-fills: venue, instrument, quantity (delta), execution_mode=\"record_only\", reason=\"Correction for break {break_id}\".\n  Also add \"View Market\" link (ArrowRight icon) on every row:\n  Navigate to `/services/trading/markets?instrument=${row.instrument_id}&venue=${row.venue}`.\n", status: done, blocked_by: p5b-recon-accept-reject-actions, note: ''}
- {id: p5d-phase5-quality-gate, content: "- [ ] [AGENT] P0. Run UI quality gates:\n  `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build`\n  `cd unified-trading-system-ui && CI=true npm test -- --run`\n", status: done, note: QG GATE — Phase 6 blocked until this passes.}
- {id: p6a-execution-service-tests, content: "- [ ] [AGENT] P1. Add tests to `execution-service/tests/unit/`:\n  1. `test_manual_record_only.py`: Test POST /manual/instruction with execution_mode=record_only → returns fill_id, no orchestrator call. Test audit log contains MANUAL_FILL_RECORDED. Test venue validation skipped for record_only.\n  2. `test_dynamic_venues.py`: Test _get_supported_venues() returns from UAC registry not hardcoded. Test GET /manual/venues returns list. Test GET /manual/algos returns dict.\n  3. `test_operational_mode_validation.py`: Test get_handler_for_operation() accepts OperationalMode values, rejects invalid strings.\n", status: done, blocked_by: p5d-phase5-quality-gate, note: ''}
- {id: p6b-recon-service-tests, content: "- [ ] [AGENT] P1. Add tests to `batch-live-reconciliation-service/tests/unit/`:\n  `test_resolution_api.py`: Test POST /reconciliation/resolve with accept/reject/investigate. Test GET /reconciliation/breaks with filters. Test POST /reconciliation/book-correction returns pre-filled request.\n", status: done, blocked_by: p5d-phase5-quality-gate, note: Can run in PARALLEL with p6a.}
- {id: p6c-ui-vitest, content: "- [ ] [AGENT] P1. Add vitest tests to `unified-trading-system-ui/__tests__/` or alongside components:\n  1. `book-page.test.tsx`: Category tab switching changes visible fields. EXECUTE/RECORD_ONLY toggle shows/hides fields. Hierarchy dropdowns render.\n  2. `recon-actions.test.tsx`: Accept/reject buttons appear for non-resolved rows. Dialog opens with note input. Mutation fires on confirm.\n  3. `manual-panel-enhanced.test.tsx`: Algo dropdown renders. Venue dropdown is dynamic. Instruction type selector visible.\n", status: done, blocked_by: p5d-phase5-quality-gate, note: Can run in PARALLEL with p6a and p6b.}
- {id: p6d-codex-documentation, content: "- [ ] [AGENT] P2. Add documentation to `unified-trading-pm (codex/ subdir)/`:\n  1. `04-architecture/manual-trade-booking.md`: Document OperationalMode enum, ManualExecutionMode, dual execution-service deployment, record-only fill pipeline, back-office vs in-context UI surfaces.\n  2. `04-architecture/reconciliation-resolution.md`: Document ReconciliationResolution schema, accept/reject/investigate workflow, book-correction flow.\n  Update `00-SSOT-INDEX.md` with pointers to new docs.\n", status: done, blocked_by: p5d-phase5-quality-gate, note: ''}
- {id: p6e-final-qg-sweep, content: "- [ ] [AGENT] P0. Full QG sweep across all 6 affected repos (SEQUENTIAL):\n  1. `cd unified-api-contracts && bash scripts/quality-gates.sh`\n  2. `cd execution-service && bash scripts/quality-gates.sh`\n  3. `cd batch-live-reconciliation-service && bash scripts/quality-gates.sh`\n  4. `cd deployment-service && bash scripts/quality-gates.sh`\n  5. `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build && CI=true npm test -- --run`\n  6. `cd unified-trading-pm && bash scripts/quality-gates.sh`\n  ALL must pass green. Zero regressions.\n", status: todo, note: FINAL GATE — plan archivable when all pass.}
isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_operational_validation_2026_04_15.plan.md](./consolidated_operational_validation_2026_04_15.plan.md).**
> Original scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Manual Trade Booking + Reconciliation Resolution

## Context

The unified trading system needs Citadel-grade manual trade booking. Three motivations:

1. **Back-office booking**: OTC trades, missed exchange fills, position simulation — recorded without venue execution
2. **In-context manual trading**: Alongside order book/candle visualization, with algo selection and all instrument
   types
3. **Reconciliation resolution**: Accept/reject breaks, with "book correcting trade" flow

The deployment cluster runs **two execution-service instances**: LIVE (automated strategies) + MANUAL (operator
booking + backup). If live goes down, manual is the backup.

## Architecture

```
                ┌─────────────────────────────────────────────────┐
                │              Deployment Cluster                  │
                │                                                  │
                │  execution-service (LIVE)     ←── strategy-svc   │
                │  execution-service (MANUAL)   ←── UI / API       │
                │                                                  │
                └─────────────────────────────────────────────────┘

  UI Surfaces:
    /services/trading/book     ─── Back-office (full page, hierarchy selectors, all categories)
    ManualTradingPanel         ─── In-context (sheet/drawer alongside order book)

  Two execution modes per manual instruction:
    EXECUTE      → route to venue via orchestrator (same as automated)
    RECORD_ONLY  → skip venue, record CanonicalFill directly (OTC/missed/simulation)

  Recon resolution flow:
    Recon page → Accept/Reject/Investigate → (Reject) → Book Correction → /services/trading/book?prefill=...
```

## Dependency DAG

```
Phase 1 (UIC schemas) ─── QG ──→ Phase 2 (exec-svc) ─── QG ──→ Phase 3 (recon-svc + deploy)
                                                                          │
                                                                   ─── QG ──→ Phase 4 (UI booking)
                                                                                    │
                                                                             ─── QG ──→ Phase 5 (UI panel + recon)
                                                                                              │
                                                                                       ─── QG ──→ Phase 6 (tests + sweep)
```

## Key Files

| File                                                                                                         | Action                                                         |
| ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| `unified-api-contracts (internal)/unified_internal_contracts/modes.py`                                       | ADD OperationalMode enum                                       |
| `unified-api-contracts (internal)/unified_internal_contracts/execution.py`                                   | ADD ManualExecutionMode, EXTEND ManualInstruction              |
| `unified-api-contracts (internal)/unified_internal_contracts/reconciliation.py`                              | CREATE ReconciliationAction + ReconciliationResolution         |
| `unified-api-contracts (internal)/unified_internal_contracts/domain/execution_service/manual_instruction.py` | DELETE (duplicate)                                             |
| `execution-service/execution_service/cli/handlers/__init__.py`                                               | VALIDATE against OperationalMode                               |
| `execution-service/execution_service/api/manual_schemas.py`                                                  | ADD execution_mode, counterparty, source_reference fields      |
| `execution-service/execution_service/api/manual_instruction_api.py`                                          | ADD record-only branch, dynamic venues, algos/venues endpoints |
| `batch-live-reconciliation-service/batch_live_reconciliation_service/api/resolution_api.py`                  | CREATE resolution endpoints                                    |
| `deployment-service/configs/clusters/*.yaml`                                                                 | ADD execution-service:manual to all 6 cluster configs          |
| `unified-trading-system-ui/app/(platform)/services/trading/book/page.tsx`                                    | CREATE back-office booking page                                |
| `unified-trading-system-ui/components/trading/manual-trading-panel.tsx`                                      | EXTEND with algos, dynamic venues, execution_mode              |
| `unified-trading-system-ui/app/(platform)/services/reports/reconciliation/page.tsx`                          | ADD accept/reject/book actions                                 |
