---
doc_type: plan
title: autonomous-recovery-and-transfer-architecture
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-16'
overview: Complete autonomous recovery matrix implementation (G1-G6), transfer architecture (CeFi internal, Copper live, CCXT, venue wallet types), UI recovery controls, auto-deleverage wiring across all domains
type: mixed
epic: epic-code-completion
completion_gates: {code: C5, deployment: D3, business: B3}
repo_gates:
- {repo: unified-api-contracts, code: C1, deployment: none, business: none}
- {repo: unified-trading-library, code: C1, deployment: none, business: none}
- {repo: execution-service, code: C1, deployment: none, business: none}
- {repo: position-balance-monitor-service, code: C1, deployment: none, business: none}
- {repo: strategy-service, code: C0, deployment: none, business: none}
- {repo: alerting-service, code: C1, deployment: none, business: none}
- {repo: unified-trading-system-ui, code: C1, deployment: none, business: none}
- {repo: unified-trading-pm, code: C1, deployment: none, business: none}
depends_on: [position-reconciliation-and-cost-preview]
todos:
- {id: uac-venue-wallet-types, content: '- [x] [AGENT] P0. UAC: Venue wallet type registry — funding/trading/spot/unified per venue, internal transfer support flag, deposit-to-trading-direct flag. Extend VenueMapping or new VenueWalletCapabilities schema.

    ', status: done}
- {id: uac-transfer-type-enum, content: '- [x] [AGENT] P0. UAC: TransferType enum (ON_CHAIN, CEX_WITHDRAWAL, CEX_INTERNAL, CUSTODY_TRANSFER) and extend TransferInstruction with transfer_type, from_wallet_type, to_wallet_type fields.

    ', status: done}
- {id: uac-recovery-event-schemas, content: '- [x] [AGENT] P0. UAC: Recovery action schemas — ReconHealthStatus (can_reconcile, can_execute, venue_connectivity), CascadeState (venues_open_count, venues_total, cascade_pct), AutoDeleverageRequest/Response.

    ', status: done}
- {id: uei-new-events, content: '- [x] [AGENT] P0. UEI: New events — DUAL_FAILURE_DETECTED, RECON_DEGRADED_CLOSE, VENUE_CASCADE_DETECTED, AUTO_DELEVERAGE_TRIGGERED, TRANSFER_INITIATED, TRANSFER_CONFIRMED, TRANSFER_FAILED, CEX_INTERNAL_TRANSFER_COMPLETED.

    ', status: done}
- {id: es-transfer-type-router, content: '- [x] [AGENT] P0. Execution-service: Transfer type router in transfer_handler.py — discriminate ON_CHAIN (→ Copper/local key), CEX_WITHDRAWAL (→ CCXT), CEX_INTERNAL (→ exchange API), CUSTODY_TRANSFER (→ Copper create_transfer). Route based on TransferType + venue capabilities from UAC.

    ', status: done}
- {id: es-cefi-internal-transfers, content: '- [x] [AGENT] P0. Execution-service: CeFi internal transfer handlers — Binance universal transfer (funding→futures, spot→futures), OKX funding→trading, Bybit unified→contract. Use CCXT transfer() or direct API. Wrap venue-specific logic behind unified interface.

    ', status: done}
- {id: es-copper-live-wiring, content: '- [x] [AGENT] P1. Execution-service: Wire Copper custody provider into live flow — custody factory returns real CopperCustodyProvider when copper config present (not mock). sign_transaction() and create_transfer() called for on-chain DeFi transfers.

    ', status: done}
- {id: es-transfer-confirmation, content: '- [x] [AGENT] P1. Execution-service: Transfer confirmation polling — after initiating transfer, poll for completion (blockchain confirmations for on-chain, exchange status for CeFi). Emit TRANSFER_CONFIRMED or TRANSFER_FAILED. Retry on transient failure.

    ', status: done}
- {id: es-funding-trading-scan, content: '- [x] [AGENT] P1. Execution-service: Scan both funding AND trading wallets on CeFi venues. When client deposits to funding wallet, auto-detect and initiate internal transfer to trading wallet. Emit DEPOSIT_DETECTED → CEX_INTERNAL_TRANSFER_COMPLETED.

    ', status: done}
- {id: g1-multi-venue-cascade, content: '- [x] [AGENT] P0. G1: Multi-venue circuit breaker cascade → auto kill switch. Execution-service: monitor all venue breaker states, when >50% venues for a strategy are OPEN, auto-activate STOP_NEW_ONLY. When all venues OPEN, firm-wide kill switch. Emit VENUE_CASCADE_DETECTED event.

    ', status: done}
- {id: g2-recon-pre-close-gate, content: '- [x] [AGENT] P0. G2: Reconciliation as pre-close gate. Execution-service: before executing any exit playbook, check PBMS /reconciliation/drift/portfolio-snapshot for recon health. If recon broken but exec works, proceed with RECON_DEGRADED_CLOSE flag + post-close verification.

    ', status: done}
- {id: g3-dual-failure-detection, content: '- [x] [AGENT] P0. G3: Dual failure detection. PBMS: detect when both reconciliation AND execution connectivity are lost. Emit DUAL_FAILURE_DETECTED (CRITICAL). Kill switch auto-activated. PagerDuty P1 + Telegram.

    ', status: done}
- {id: g4-drift-auto-stop-new, content: '- [x] [AGENT] P1. G4: Position drift CRITICAL → auto STOP_NEW_ONLY. PBMS drift monitor: on CRITICAL severity, call execution-service kill switch API with scope={strategy_id, exit_type=STOP_NEW_ONLY}. Strategy pauses target-tracking.

    ', status: done}
- {id: g5-connectivity-stale-recon, content: '- [x] [AGENT] P1. G5: Connectivity loss → mark recon stale. PBMS: subscribe to CIRCUIT_BREAKER_OPEN events. When venue circuit breaker opens, mark that venue''s reconciliation data as stale/unreliable in the portfolio snapshot.

    ', status: done}
- {id: g6-playbook-scenario-mapping, content: '- [x] [AGENT] P1. G6: Playbook-to-scenario mapping. UAC: config mapping from trigger scenario (HF_CRITICAL, VENUE_CASCADE, DRIFT_CRITICAL, DUAL_FAILURE) → EmergencyExitPlaybook. Execution-service uses this to auto-select playbook.

    ', status: done}
- {id: auto-deleverage-cefi, content: '- [x] [AGENT] P1. CeFi auto-deleverage: When HF 1.0-1.2 on CeFi venue (margin call zone), strategy-service emits reduce-position instructions. Execution-service submits market close orders to reduce leverage. Not flash-loan based (that''s DeFi only). Wire HF threshold → instruction → execution for CeFi.

    ', status: done}
- {id: auto-deleverage-tradfi, content: '- [x] [AGENT] P2. TradFi auto-deleverage: Same pattern as CeFi but for TradFi venues (CME, CBOE). Margin models differ (SPAN margin). Wire margin breach → reduce position.

    ', status: done}
- {id: treasury-auto-transfer, content: '- [x] [AGENT] P1. Treasury auto-transfer: When TREASURY_LOW event fires, PBMS compute_rebalance_amounts() already calculates targets. Wire this to strategy-service to emit TransferInstruction with correct TransferType. Strategy → execution-service → actual transfer.

    ', status: done}
- {id: ui-observe-recovery-controls, content: '- [x] [AGENT] P0. UI: Observe tab — Recovery Controls page. Human can manually trigger ANY autonomous action: activate/deactivate kill switch (scoped), trip/reset circuit breaker per venue, trigger reconciliation, force deleverage, initiate transfer, trigger drift evaluation. All actions require rationale field. Live-mode only.

    ', status: done}
- {id: ui-observe-circuit-breaker-dashboard, content: '- [x] [AGENT] P1. UI: Observe tab — Circuit Breaker Dashboard. Per-venue breaker state (CLOSED/DEGRADED/OPEN/HALF_OPEN), failure rate %, cooldown timer, backoff cycle count, queue depth. Manual force-open/force-close buttons.

    ', status: done}
- {id: ui-observe-transfer-monitor, content: '- [x] [AGENT] P1. UI: Observe tab — Transfer Monitor. Active transfers with status (initiated/pending/confirmed/failed), confirmation progress, venue wallet balances (funding + trading), treasury reserve %. Manual transfer initiation button.

    ', status: done}
- {id: ui-observe-health-factor-panel, content: '- [x] [AGENT] P1. UI: Observe tab — Health Factor Panel. Per-strategy, per-venue HF with threshold bands (green/yellow/orange/red). Deleverage button per position. DeFi + CeFi + TradFi unified view.

    ', status: done}
- {id: ui-alert-feed-recovery-events, content: '- [x] [AGENT] P1. UI: Observe → Alerts tab — filter for recovery events. Show all autonomous recovery actions with severity, action taken, result. Human can acknowledge/override from alert feed.

    ', status: done}
- {id: alerting-routing-complete, content: '- [x] [AGENT] P0. Alerting-service: routing rules updated with all recovery events (T1-T4 tiers). 20+ explicit patterns, *-fallback ensures nothing silent.

    ', status: done}
- {id: codex-kill-switch-updated, content: '- [x] [AGENT] P0. Codex: kill-switch-circuit-breaker.md updated — DEGRADED state, exponential backoff, scoped kill switches, multi-venue handling, strategy pausing, reconciliation gate.

    ', status: done}
- {id: codex-recovery-matrix-created, content: '- [x] [AGENT] P0. Codex: autonomous-recovery-matrix.md created — full decision tree, multi-venue hedged positions, reconciliation 2x2 matrix, gap status.

    ', status: done}
- {id: codex-alerting-updated, content: '- [x] [AGENT] P0. Codex: alerting.md updated — every autonomous recovery action mapped to alert tier, routing rules documented, Telegram primary.

    ', status: done}
- {id: codex-transfer-architecture, content: '- [x] [AGENT] P1. Codex: transfer-architecture.md — new doc covering transfer type discrimination (on-chain/CEX withdrawal/CeFi internal/custody), venue wallet capabilities, funding→trading flows per venue, Copper vs local key, treasury→trading flow.

    ', status: done}
- {id: qg-all-repos, content: '- [x] [AGENT] P0. Quality gates pass on all affected repos.

    ', status: done}
isProject: false
---

# Autonomous Recovery & Transfer Architecture — Complete Implementation

## Context

This plan completes the autonomous recovery stack and transfer architecture. It builds on the position reconciliation
work (previous plan) and closes all identified gaps. The goal: the system handles itself 99.9% of the time. Human
intervention only for the 0.1% dual-failure case.

**Two major workstreams:**

1. **Autonomous Recovery (G1-G6):** Multi-venue cascade → kill switch, reconciliation pre-close gate, dual failure
   detection, drift → auto stop, connectivity → stale recon, playbook mapping.

2. **Transfer Architecture:** Transfer type discrimination (on-chain / CeFi withdrawal / CeFi internal / custody), venue
   wallet capabilities (funding vs trading), Copper live wiring, CeFi internal transfers (Binance funding→futures, OKX
   funding→trading, Bybit routing), confirmation polling, treasury auto-transfer wiring.

Plus: UI controls for human override of every autonomous action, auto-deleverage wiring for CeFi/TradFi, complete
alerting routing.

## Pre-Audit: What Exists vs What's Missing

### Transfer Architecture

| Component                      | Status           | Gap                                                     |
| ------------------------------ | ---------------- | ------------------------------------------------------- |
| TransferInstruction (UAC)      | REAL but generic | No transfer_type, no wallet type routing                |
| Venue withdrawal schemas (UAC) | PARTIAL          | Binance/OKX/Bybit schemas exist, not used               |
| transfer_handler.py (ES)       | STUB             | Computes costs, returns immediately, no actual transfer |
| Copper API client (ES)         | REAL             | Full implementation but never instantiated in live      |
| Copper custody factory         | STUB             | Falls back to MockCustodyProvider                       |
| Fireblocks                     | STUB             | Always returns mock                                     |
| CeFi internal transfers        | NOT IMPL         | OKX/Binance/Bybit schemas exist, no handler             |
| CCXT withdraw                  | NOT IMPL         | No wrapper in transfer_handler                          |
| Confirmation polling           | NOT IMPL         | Returns immediately                                     |
| Treasury monitor               | REAL             | Computes + emits events, doesn't trigger transfers      |
| Wallet config (DeFi)           | REAL             | Full schema for treasury + trading per share class      |

### Autonomous Recovery Gaps

| Gap | Description                                  | Status   |
| --- | -------------------------------------------- | -------- |
| G1  | Circuit breaker cascade → kill switch        | NOT IMPL |
| G2  | Reconciliation pre-close gate                | NOT IMPL |
| G3  | Dual failure detection (recon + exec)        | NOT IMPL |
| G4  | Position drift CRITICAL → auto STOP_NEW_ONLY | NOT IMPL |
| G5  | Connectivity loss → stale recon marking      | NOT IMPL |
| G6  | Playbook-to-scenario mapping                 | NOT IMPL |

### Auto-Deleverage

| Domain | Status      | Gap                                              |
| ------ | ----------- | ------------------------------------------------ |
| DeFi   | IMPLEMENTED | Flash loan atomic deleverage in intent_engine.py |
| CeFi   | SCHEMA ONLY | HF thresholds defined, no instruction wiring     |
| TradFi | SCHEMA ONLY | SPAN margin model defined, no instruction wiring |

### UI Recovery Controls

| Control                         | Status                         | Gap                                               |
| ------------------------------- | ------------------------------ | ------------------------------------------------- |
| Kill switch activate/deactivate | EXISTS (kill-switch-panel.tsx) | In Trading, not Observe                           |
| Circuit breaker per-venue       | NOT IN UI                      | No dashboard or manual controls                   |
| Transfer monitor                | NOT IN UI                      | No visibility into active transfers               |
| Health factor panel             | PARTIAL (risk page greeks)     | No deleverage button, no CeFi/TradFi unified view |
| Recovery action feed            | NOT IN UI                      | Alerts exist but no recovery-specific filtering   |

## Execution Phases

```
Phase 0: UAC Schemas + UEI Events ─────────────────────────────────
  ├─ Venue wallet types + capabilities
  ├─ TransferType enum + extended TransferInstruction
  ├─ Recovery schemas (ReconHealthStatus, CascadeState)
  └─ New UEI events (8 events)
         ┌─────────────── QG GATE ───────────────────┐

Phase 1: Transfer Architecture (PARALLEL) ──────────────────────────
  ├─ Transfer type router in transfer_handler
  ├─ CeFi internal transfer handlers
  ├─ Copper live wiring (custody factory)
  ├─ Confirmation polling
  └─ Funding→trading auto-scan

Phase 2: Recovery Gaps G1-G6 (PARALLEL) ────────────────────────────
  ├─ G1: Multi-venue cascade → kill switch
  ├─ G2: Recon pre-close gate
  ├─ G3: Dual failure detection
  ├─ G4: Drift → auto STOP_NEW_ONLY
  ├─ G5: Connectivity → stale recon
  └─ G6: Playbook-to-scenario mapping

Phase 3: Auto-Deleverage Wiring (PARALLEL) ─────────────────────────
  ├─ CeFi auto-deleverage (margin → reduce position)
  ├─ TradFi auto-deleverage (SPAN margin → reduce)
  └─ Treasury auto-transfer wiring (TREASURY_LOW → transfer)
         ┌─────────────── QG GATE ───────────────────┐

Phase 4: UI Recovery Controls (PARALLEL) ───────────────────────────
  ├─ Recovery Controls page (manual trigger any action)
  ├─ Circuit Breaker Dashboard (per-venue state)
  ├─ Transfer Monitor (active transfers, balances)
  ├─ Health Factor Panel (unified CeFi/DeFi/TradFi)
  └─ Alert Feed recovery event filter
         ┌─────────────── QG GATE ───────────────────┐

Phase 5: Codex Doc ─────────────────────────────────────────────────
  └─ transfer-architecture.md (new)

Phase 6: QG All Repos ─────────────────────────────────────────────
```

## Venue Wallet Capabilities (UAC Schema Design)

```python
class VenueWalletCapabilities(BaseModel, frozen=True):
    """Per-venue knowledge of wallet structure and transfer capabilities."""

    venue: str
    # Wallet types available on this venue
    has_funding_wallet: bool          # Binance=True, OKX=True, Bybit=True, DeFi=False
    has_trading_wallet: bool          # Binance-Futures=True, OKX-Trading=True
    has_spot_wallet: bool             # Binance-Spot=True
    has_unified_account: bool         # Bybit=True (unified account), OKX=True (unified)
    deposits_to: str                  # "funding" | "trading" | "unified" — where deposits land

    # Internal transfer support
    supports_internal_transfer: bool  # Can move between funding↔trading
    internal_transfer_instant: bool   # True for all CeFi (instant), False for on-chain

    # External transfer support
    supports_withdrawal: bool
    supports_deposit: bool
    withdrawal_requires_whitelist: bool

    # Custody
    custody_provider: str | None      # "copper" | "fireblocks" | None (direct)
```

Example configurations:

- Binance: `deposits_to="funding", has_funding_wallet=True, has_trading_wallet=True, supports_internal_transfer=True`
- OKX: `deposits_to="funding", has_funding_wallet=True, has_trading_wallet=True, supports_internal_transfer=True`
- Bybit: `deposits_to="unified", has_unified_account=True, supports_internal_transfer=True`
- Aave (DeFi): `deposits_to="trading", has_funding_wallet=False, custody_provider="copper"`

## Transfer Type Router Logic

```
TransferInstruction arrives at execution-service
  |
  +-- Classify transfer type:
  |   |
  |   +-- Same venue, different wallet type?
  |   |   → CEX_INTERNAL (e.g., Binance funding→futures)
  |   |   → Use exchange internal transfer API
  |   |
  |   +-- Different CeFi venues?
  |   |   → CEX_WITHDRAWAL (e.g., Binance→OKX)
  |   |   → Use CCXT withdraw on source, deposit on dest
  |   |
  |   +-- CeFi → DeFi or DeFi → CeFi?
  |   |   → ON_CHAIN if local key, CUSTODY_TRANSFER if Copper
  |   |   → Use Copper sign_transaction() or local key signing
  |   |
  |   +-- DeFi → DeFi (same chain)?
  |   |   → ON_CHAIN (direct transfer)
  |   |
  |   +-- DeFi → DeFi (cross chain)?
  |       → BRIDGE (use bridge_cost_model for cost, bridge protocol for execution)
  |
  +-- Execute via appropriate handler
  +-- Poll for confirmation (async)
  +-- Emit TRANSFER_CONFIRMED or TRANSFER_FAILED
  +-- If CeFi deposit lands in funding → auto CEX_INTERNAL to trading
```

## CeFi Internal Transfer APIs

| Venue   | API                                    | From        | To                 | CCXT Method |
| ------- | -------------------------------------- | ----------- | ------------------ | ----------- |
| Binance | POST /sapi/v1/asset/transfer           | MAIN (spot) | UMFUTURE (futures) | transfer()  |
| OKX     | POST /api/v5/asset/transfer            | 6 (funding) | 18 (trading)       | transfer()  |
| Bybit   | POST /v5/asset/transfer/inter-transfer | FUND        | UNIFIED            | transfer()  |

All are instant. No blockchain confirmation needed.

## Success Criteria

| KPI                            | Target                                         |
| ------------------------------ | ---------------------------------------------- |
| Transfer type discrimination   | 100% of transfers classified correctly by type |
| CeFi internal transfer latency | < 5s (exchange API round-trip)                 |
| On-chain transfer confirmation | < 5 min (12 confirmations ETH)                 |
| G1 cascade detection latency   | < 10s from 2nd venue OPEN to kill switch       |
| G3 dual failure detection      | < 30s from both conditions met                 |
| UI recovery action latency     | < 2s from button click to API call             |
| Alert delivery                 | < 5s from event to Telegram notification       |
| Auto-deleverage trigger        | < 30s from HF breach to instruction emission   |
