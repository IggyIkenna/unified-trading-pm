---
doc_type: plan
title: recovery-and-transfer-completion
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-16'
overview: Complete all stubbed execution paths, strategy-service integration, UI→backend wiring, CeFi/TradFi auto-deleverage, G6 playbook mapping — batch and live share identical code paths
type: mixed
epic: epic-code-completion
completion_gates: {code: C5, deployment: D3, business: B3}
repo_gates:
- {repo: execution-service, code: C0, deployment: none, business: none}
- {repo: strategy-service, code: C0, deployment: none, business: none}
- {repo: position-balance-monitor-service, code: C0, deployment: none, business: none}
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
depends_on: [autonomous-recovery-and-transfer-architecture]
todos:
- {id: es-adapter-protocol, content: '- [x] [AGENT] P0. Execution-service: TransferAdapter protocol — define protocol/interface with execute_transfer(), get_balance(), poll_status() methods. Two implementations: LiveTransferAdapter (real CCXT/Copper) and MockTransferAdapter (immediate success, simulated delays). Batch mode gets MockTransferAdapter, live gets LiveTransferAdapter. Injected via factory based on execution mode.

    ', status: done}
- {id: es-live-ccxt-adapter, content: '- [x] [AGENT] P0. Execution-service: LiveCcxtTransferAdapter — real CCXT wrapper for CeFi. Implements internal_transfer() via ccxt.transfer(), withdraw() via ccxt.withdraw(), get_balance() via ccxt.fetch_balance(). Uses ApiKeyReloader for hot-reloaded credentials. Handles venue-specific params from VenueWalletCapabilities.ccxt_transfer_params.

    ', status: done}
- {id: es-live-custody-adapter, content: '- [x] [AGENT] P0. Execution-service: LiveCustodyTransferAdapter — wires real Copper client (already exists in custody/copper.py). custody factory returns CopperCustodyProvider when copper config present (not mock). create_transfer() and sign_transaction() called for on-chain/custody transfers.

    ', status: done}
- {id: es-transfer-confirmation-poller, content: '- [x] [AGENT] P0. Execution-service: TransferConfirmationPoller — async polling loop. For ON_CHAIN: poll blockchain for N confirmations (12 ETH, 1 L2). For CEX_WITHDRAWAL: poll exchange withdrawal status API. For CUSTODY: poll Copper transaction status. Configurable timeout (default 30min). Emits TRANSFER_CONFIRMED or TRANSFER_FAILED. In batch mode: MockTransferAdapter returns instant confirmation.

    ', status: done}
- {id: es-transfer-handler-wire, content: '- [x] [AGENT] P0. Execution-service: Wire adapters into transfer_handler.py — replace stub execution methods with adapter calls. inject_adapter(mode) at startup based on ExecutionMode (LIVE/BACKTEST/PAPER). Same code path for all modes, adapter implementation differs.

    ', status: done}
- {id: ss-kill-switch-pause, content: '- [x] [AGENT] P0. Strategy-service: Kill switch target-tracking pause. When KILL_SWITCH_ACTIVATED event received, pause the target-tracking loop for affected scope. Strategy stops emitting new signals but does NOT fight back to target position. Resume on KILL_SWITCH_DEACTIVATED. Same in batch (mock kill switch state) and live.

    ', status: done}
- {id: ss-treasury-rebalance-consumer, content: '- [x] [AGENT] P0. Strategy-service: Consume TREASURY_REBALANCE_NEEDED events. When received, generate TransferInstruction with correct TransferType (from UAC classify_transfer_type). Emit to execution-service. In batch: instruction processed by MockTransferAdapter. In live: processed by LiveCcxtTransferAdapter/LiveCustodyTransferAdapter.

    ', status: done}
- {id: ss-deposit-to-trading, content: '- [x] [AGENT] P1. Strategy-service: Consume DEPOSIT_DETECTED events. Check VenueWalletCapabilities.requires_internal_transfer. If true, emit TransferInstruction with TransferType.CEX_INTERNAL. Execution-service handles the actual funding→trading move.

    ', status: done}
- {id: ss-auto-deleverage-cefi, content: '- [x] [AGENT] P0. Strategy-service: CeFi auto-deleverage wiring. RiskMonitor already receives HF data from PBMS. When HF 1.0-1.2 on CeFi venue: emit reduce-position StrategyInstruction (MARKET_ORDER, reduce quantity proportional to HF breach). Not flash-loan (that''s DeFi only). Same code path batch/live — in batch the order executes against simulated book.

    ', status: done}
- {id: ss-auto-deleverage-tradfi, content: '- [x] [AGENT] P1. Strategy-service: TradFi auto-deleverage. Same pattern as CeFi. SPAN margin model thresholds from config. Emit reduce-position instruction when margin breach detected. Wire margin state → threshold check → instruction emission.

    ', status: done}
- {id: ss-exit-playbook-executor, content: '- [x] [AGENT] P1. Strategy-service: Exit playbook executor. When kill switch activates with a specific EmergencyExitType (FAST_UNWIND, DELTA_HEDGE, etc.), strategy emits the correct sequence of close/hedge instructions per the playbook steps. In batch: same instruction sequence, mock execution.

    ', status: done}
- {id: pbms-kill-switch-http, content: '- [x] [AGENT] P0. PBMS: Wire the G4 kill switch activation HTTP call. Add execution_service_url to config (from UnifiedCloudConfig). In drift monitor, when CRITICAL: make real HTTP POST to /kill-switch/activate with scoped payload. In batch mode: log the call without making it (or call a mock endpoint).

    ', status: done}
- {id: g6-playbook-mapping, content: '- [x] [AGENT] P1. UAC: Playbook-to-scenario config mapping. New dataclass PlaybookTriggerMapping: trigger_scenario (HF_CRITICAL, VENUE_CASCADE, DRIFT_CRITICAL, DUAL_FAILURE, TREASURY_LOW) → EmergencyExitType + default parameters. Registry dict PLAYBOOK_TRIGGER_MAP. Execution-service recon_gate and cascade_monitor use this to auto-select playbook.

    ', status: done}
- {id: ui-hooks-reconciliation, content: '- [x] [AGENT] P0. UI: API hooks for Position Reconciliation page. useReconciliationSnapshot() → GET /reconciliation/drift/portfolio-snapshot (PBMS). useReconciliationHistory() → GET /reconciliation/drift/history (PBMS). In mock mode: return existing mock data. In live mode: fetch from PBMS API.

    ', status: done}
- {id: ui-hooks-cost-preview, content: '- [x] [AGENT] P0. UI: API hooks for cost preview. useUnwindPreview(request) → POST /preview/unwind (execution-service). Wire into intervention-controls.tsx and kill-switch-panel.tsx to replace static mock data with live API calls. In mock mode: return getMockCostPreview().

    ', status: done}
- {id: ui-hooks-recovery-controls, content: '- [x] [AGENT] P0. UI: API hooks for Recovery Controls page. useKillSwitchStatus() → GET /kill-switch/status. useKillSwitchMutation() → POST /kill-switch/activate|deactivate. useCircuitBreakerStates() → GET /circuit-breakers (new endpoint needed). useActiveTransfers() → GET /transfers/active (new endpoint needed). useHealthFactors() → GET /reconciliation/drift/portfolio-snapshot. In mock mode: return existing mock fixtures.

    ', status: done}
- {id: ui-hooks-client-reporting, content: '- [x] [AGENT] P1. UI: API hooks for client-reporting close-all. useCloseAll(clientId) → POST /api/v1/emergency/close-all/{client_id}. Dry-run toggle. In mock mode: return simulated results.

    ', status: done}
- {id: es-circuit-breaker-api, content: '- [x] [AGENT] P1. Execution-service: GET /circuit-breakers endpoint — returns per-venue breaker state (state, failure_rate, cooldown_remaining, backoff_cycle). POST /circuit-breakers/{venue}/force-open and POST /circuit-breakers/{venue}/force-close for manual override. Wire into existing app.py.

    ', status: done}
- {id: es-transfers-api, content: '- [x] [AGENT] P1. Execution-service: GET /transfers/active endpoint — returns list of in-flight transfers with status, type, from/to venue, amount, initiated_at. For the UI Transfer Monitor.

    ', status: done}
- {id: cr-trading-key-config, content: '- [x] [AGENT] P2. Client-reporting-api: has_trading_capability() reads from credentials registry. Add has_trading_keys field to client config schema. When true, emergency close-all uses trade-prefixed secrets from Secret Manager. Document the provisioning process.

    ', status: done}
- {id: qg-all-repos, content: '- [x] [AGENT] P0. Quality gates pass on all affected repos.

    ', status: done}
isProject: false
---

# Recovery & Transfer Completion — All Remaining Work

## Core Principle: Batch = Live, Same Code Paths

Every flow — transfers, kill switches, auto-deleverage, reconciliation — follows the **exact same code path** in batch
and live mode. The ONLY difference is which adapter implementation is injected:

```
                         ┌─────────────────────────────┐
                         │   TransferHandler            │
                         │   (same code always)         │
                         └──────────┬──────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            ┌───────▼────────┐             ┌───────▼────────┐
            │ LiveTransfer   │             │ MockTransfer   │
            │ Adapter        │             │ Adapter        │
            │                │             │                │
            │ - Real CCXT    │             │ - Instant OK   │
            │ - Real Copper  │             │ - Simulated    │
            │ - Real polling │             │   delays       │
            │ - Real fees    │             │ - Zero fees    │
            └────────────────┘             └────────────────┘
                 LIVE mode                   BATCH/BACKTEST
```

Same pattern for:

- Kill switch: real HTTP call (live) vs state flag (batch)
- Auto-deleverage: real market order (live) vs simulated fill (batch)
- Circuit breakers: real venue health (live) vs simulated failures (batch)
- Reconciliation: real PBMS query (live) vs mock snapshot (batch)

This means:

1. **All business logic is testable in batch** — same code, mock adapters
2. **No batch-only or live-only code paths** — if it works in batch, it works in live
3. **Adapter injection at startup** based on ExecutionMode (from config)

## What's Remaining (Honest Assessment)

### Execution-service (5 items)

1. TransferAdapter protocol + MockTransferAdapter + factory
2. LiveCcxtTransferAdapter (real CCXT wrapper)
3. LiveCustodyTransferAdapter (wire real Copper)
4. TransferConfirmationPoller (async polling)
5. Wire adapters into transfer_handler.py

### Strategy-service (6 items — currently 0 changes)

1. Kill switch target-tracking pause
2. TREASURY_REBALANCE_NEEDED event consumer
3. DEPOSIT_DETECTED → CEX_INTERNAL TransferInstruction
4. CeFi auto-deleverage (HF breach → reduce-position instruction)
5. TradFi auto-deleverage (SPAN margin breach)
6. Exit playbook executor (kill switch → close/hedge instruction sequence)

### PBMS (1 item)

1. Wire G4 kill switch HTTP call (real httpx call with config URL)

### UAC (1 item)

1. G6 PlaybookTriggerMapping config

### UI (4 items)

1. API hooks for Position Reconciliation page
2. API hooks for cost preview (wire into intervention controls)
3. API hooks for Recovery Controls page
4. API hooks for client-reporting close-all

### Execution-service new endpoints (2 items)

1. GET /circuit-breakers (for UI dashboard)
2. GET /transfers/active (for UI transfer monitor)

### Client-reporting (1 item)

1. Trading key provisioning via credentials registry

## Execution Phases

```
Phase 1: Transfer Adapters (ES) ────────────────────────────────────
  ├─ TransferAdapter protocol + Mock + factory
  ├─ LiveCcxtTransferAdapter
  ├─ LiveCustodyTransferAdapter
  ├─ TransferConfirmationPoller
  └─ Wire into transfer_handler.py
         ┌─────────────── QG GATE ───────────────────┐

Phase 2: Strategy-Service (PARALLEL with Phase 3) ─────────────────
  ├─ Kill switch pause
  ├─ Treasury rebalance consumer
  ├─ Deposit → internal transfer
  ├─ CeFi auto-deleverage
  ├─ TradFi auto-deleverage
  └─ Exit playbook executor

Phase 3: PBMS + UAC (PARALLEL with Phase 2) ───────────────────────
  ├─ PBMS kill switch HTTP call
  └─ UAC G6 playbook mapping
         ┌─────────────── QG GATE ───────────────────┐

Phase 4: Backend Endpoints for UI (ES) ─────────────────────────────
  ├─ GET /circuit-breakers
  └─ GET /transfers/active

Phase 5: UI → Backend Wiring ───────────────────────────────────────
  ├─ Reconciliation hooks
  ├─ Cost preview hooks
  ├─ Recovery controls hooks
  └─ Client reporting hooks
         ┌─────────────── QG GATE ───────────────────┐

Phase 6: Client Reporting Trading Keys ─────────────────────────────
  └─ has_trading_keys provisioning

Phase 7: QG All Repos ─────────────────────────────────────────────
```

## Success Criteria

| KPI                            | Target                                                 |
| ------------------------------ | ------------------------------------------------------ |
| Batch/live code path parity    | 100% — zero batch-only or live-only branches           |
| Transfer adapter injection     | Factory selects correct adapter based on ExecutionMode |
| CeFi internal transfer (live)  | < 5s via CCXT transfer()                               |
| On-chain transfer confirmation | < 5 min (12 ETH blocks)                                |
| Kill switch pause propagation  | < 5s from event to strategy pause                      |
| Auto-deleverage trigger        | < 30s from HF breach to instruction emission           |
| UI hook mock/live toggle       | VITE_MOCK_API=true uses mock data, false uses API      |
