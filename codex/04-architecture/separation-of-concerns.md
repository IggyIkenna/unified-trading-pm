---
doc_type: codex-ssot
title: "Separation of Concerns: Three-Layer Architecture"
summary:
  Three-layer architecture (UAC contracts / interface adapters / T3 services) with allowed-import rules, plus the PBMS
  single-canonical positions+balances ledger invariant every consumer reads through (never a shadow copy).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    batch-live-reconciliation-service,
    execution-service,
    instruments-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-api,
  ]
scope: [engineer, admin]
tags: [uac, contracts, ssot, positions, execution]
related:
  [
    /codex/02-data/contracts-scope-and-layout.md,
    /codex/04-architecture/schema-placement.md,
    /codex/04-architecture/batch-live-architecture.md,
  ]
created: 2026-03-27
authoritative_for:
  [
    contracts/interface/service three-layer separation of concerns,
    PBMS single-canonical positions+balances ledger invariant,
  ]
referenced_by:
  [
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/reconciliation-resolution.md,
    /codex/04-architecture/schema-placement.md,
    /codex/10-audit/CONTRACTS_SEPARATION_AUDIT.md,
    /codex/15-runbooks/position-reconciliation-deploy-gate.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Separation of Concerns: Three-Layer Architecture

## Layer Model

| Layer                    | Repos                                                                                                                  | Responsibility                                                                                                                          | Allowed imports                                                                                                                                             |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Contracts (T0)**       | unified-api-contracts (UAC) — canonical/external surface + `unified_api_contracts.internal` subpackage                 | Schema definitions. UAC canonical = external API schemas + canonical normalization. UAC internal = internal service-to-service schemas. | UAC canonical/external: no deps except pydantic. UAC internal: depends on UAC canonical only.                                                               |
| **Active Service Repos** | UMI, execution-service (CeFi+DeFi+Sports), instruments-service (ref data), position-balance-monitor-service, UFI, USRI | Venue connectivity + canonical routing. Each interface owns adapters for a domain (market data, execution, etc.).                       | Import from UAC (schemas + normalizers), UTL (infrastructure). Never define schemas.                                                                        |
| **Services (T3)**        | All _-service, _-api repos                                                                                             | Business logic. Consume canonical types from interfaces.                                                                                | Import from UTL (infrastructure), interfaces (canonical output), UAC canonical + UAC internal (type annotations). Never import from UAC external/{source}/. |

## Key Rules

1. **UAC owns all external schemas and normalization.** If a venue's API response needs a Pydantic model, it goes in
   `unified_api_contracts/external/{source}/schemas.py`. The normalizer goes in `external/{source}/normalize.py`.

2. **UIC owns all internal cross-service contracts.** If two services communicate (via PubSub, REST, or shared state),
   the message schema goes in UIC.

3. **Interfaces are adapters, not schema owners.** An interface adapter calls the external API, validates against UAC
   raw schemas, normalizes to UAC canonical types, and returns the canonical object. It does NOT define new schema
   types.

4. **Services consume canonical output only.** A service receives `CanonicalTicker`, `CanonicalOrder`, etc. from
   interfaces. It never parses raw API payloads or imports from `unified_api_contracts.external.{source}`.

5. **UAC and UIC are independent.** UAC cannot import from UIC. UIC can import from UAC (canonical types are shared).
   This prevents circular dependencies.

## Import Surface Rules

See `unified-trading-pm/codex/02-data/contracts-scope-and-layout.md` section UAC Citadel Architecture for the full
import surface specification.

## Quality Gate Enforcement

- STEP 5.23 in `base-service.sh` and `base-library.sh` blocks deep UAC imports (`canonical.*`, `normalize_utils.*`,
  `config.*`, `shared.*`, `schemas.*`)
- Exempt repos: UAC (self), UIC (canonical neighbor), SIT (test harness)
- Auto-detected by `PACKAGE_NAME`/`SERVICE_NAME` in base scripts

---

## Positions SSOT — PBMS canonical ledger (codified 2026-05-12 per slot 8 audit PB-7)

> **REPO MERGE 2026-05-27 (per BLRS audit
> `plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md`)**: `position-balance-monitor-service` is
> **no longer a standalone repo** — it was merged into `strategy-service/strategy_service/position/` on 2026-05-20
> (`workspace-manifest.json:231`). Read "PBMS" below as that module. Its query API now lives at
> `strategy-service/strategy_service/position/api/routes/` (`pnl_series.py`, `positions_health.py`, `nav_snapshot.py`) +
> `api/reconciliation_routes.py` (`/reconciliation/snapshots/history`). The single-canonical-ledger invariant is
> unchanged; only the hosting repo moved. (Stale standalone-PBMS manifest stanza at lines 1120/1159 +
> `unified-trading-api/services/pbm_performance.py` endpoint base are pending owner cleanup.)

> **Invariant**: the **single canonical ledger** for positions + balances in the workspace is PBMS (now
> `strategy-service/position`). Every consumer reads positions through it — never a local copy.

Equivalent in shape to the existing CLAUDE.md rule for reference data (_"services use instruments-service for reference
data, not MTDS"_), but applied to the positions axis.

### The rule

- PBMS owns the canonical position / balance ledger. Sources of truth: live fills from execution-service +
  custody-provider `get_balance()` pings (see [`custody-providers.md`](custody-providers.md) §11) + manual ledger
  overrides via DART.
- Every consumer service reads positions from PBMS via its query API + Pub/Sub NAV snapshots — **never** maintains a
  parallel position store, a "local cache of authoritative positions," or a private fills ledger.
- The dual-projection that PBMS exposes externally:
  - **Balances projection** — per-(wallet, asset, venue) ladder reconciled against custody + venue reads on the 5-min
    ping cadence (BALANCE_DRIFT alerting per
    [`/codex/15-runbooks/alerting/balance_drift.md`](/codex/15-runbooks/alerting/balance_drift.md)).
  - **Position-lineage projection** — per-`client_id` (top-level) and per-`client_order_id` (per-order) lineage consumed
    by strategy / risk / pnl-attribution / batch-live-reconciliation. Per slot 8 audit PB-3 (`audit-logging.md`
    IMMEDIATE), execution-side audit records are _order-keyed_ (the third arg to `persist_audit_log()` is currently
    `client_order_id`); the long-term shape threads real `client_id` through so both projections key off the same axis.

### Consumer matrix

| Consumer                          | Reads positions via                                       | Writes positions?                  |
| --------------------------------- | --------------------------------------------------------- | ---------------------------------- |
| strategy-service                  | PBMS query API + Pub/Sub NAV snapshots                    | NO                                 |
| risk-and-exposure-service         | PBMS query API (pre-flight checks)                        | NO                                 |
| pnl-attribution-service           | PBMS query API + execution fills                          | NO                                 |
| batch-live-reconciliation-service | PBMS query API (canonical baseline for batch ↔ live diff) | NO                                 |
| execution-service                 | publishes fills → PBMS state-update path                  | NO (publishes, does not own state) |
| position-balance-monitor-service  | OWNS state; absorbs fills + custody pings                 | YES (sole writer)                  |

### Anti-patterns (banned)

- Any non-PBMS service holding `positions: dict[str, Position]` / `class PositionStore` / `class FillsLedger` as
  long-lived authoritative state. Caches with a TTL bounded by the next PBMS query are acceptable; long-lived shadow
  ledgers are not.
- Branching on `OperationalMode` inside PBMS source (PBMS is mode-blind by construction — see slot 8 audit PB-19 P2 for
  the POST_CUTOVER QG ratchet that flags `if mode == "live"` in `position_balance_monitor_service/`).
- Strategy / risk / execution code that bypasses PBMS to read venue balances directly during the trading hot path.
  Out-of-band balance reads for diagnostics are fine; trading decisions go through PBMS.

### Composes with

- [`batch-live-architecture.md`](batch-live-architecture.md) — PBMS is mode-blind; the 4-seam SSOT applies identically
  across batch / paper / live.
- [`paper-vs-live-execution-seam.md`](paper-vs-live-execution-seam.md) — PBMS is on the _mode-blind_ side of the seam
  (position state-update happens identically; only the fill source differs).
- [`reconciliation-resolution.md`](reconciliation-resolution.md) — batch-live reconciliation reads PBMS as the positions
  baseline (see § "Reconciliation contract — batch ↔ live").
- [`custody-providers.md`](custody-providers.md) §11 — custody-ping loop is the upstream signal that keeps the balances
  projection honest.

### Pending follow-ups (slot 8 audit)

- **PB-19 POST_CUTOVER** — codify a QG ratchet that statically flags `OperationalMode` / `pipeline_mode` branching in
  `position_balance_monitor_service/` engine/core. Mode-blindness is a CRITICAL invariant per CLAUDE.md `batch = live`;
  today it's asserted in prose but unenforced.
