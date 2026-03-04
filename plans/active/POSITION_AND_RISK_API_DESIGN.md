# Position-and-Risk-API Design Discussion

**Status:** Draft for discussion  
**Created:** 2026-03-04  
**Context:** settlement-ui alignment; codex/topology update for API service roles

---

## 1. Problem Statement

### Current Mismatch

The codex and UI-DEPENDENCY-MATRIX currently route **settlement-ui** to **execution-results-api** (ERA). This is a **weird choice**:

- **execution-results-api** = HFT analytics on orders and trades; SSOT for our **internal unreconciled** view of trades
- **Position monitor** reconciles trades against exchange and converts into positions; it owns SSOT for **actual reconciled positions**
- **Settlement, PnL, risk, strategy** UIs should consume **reconciled position data**, not raw execution analytics

### Architectural Convention

Prod services should **not directly serve UIs**. UIs route through backend APIs that:

- Can serve one of many frontends
- Aggregate domain data from one or many services
- Enforce auth, rate limits, and typed contracts

This convention needs to be documented in codex wherever we discuss repo roles, responsibilities, naming, and rules.

---

## 2. Current State

| API Service           | Port | Domain Data Source               | Serves UIs                                                   |
| --------------------- | ---- | -------------------------------- | ------------------------------------------------------------ |
| execution-results-api | 8002 | execution-service (trades/fills) | trading-analytics, strategy, execution-analytics, settlement |
| client-reporting-api  | 8003 | pnl-attribution-service          | client-reporting-ui                                          |
| market-data-api       | 8004 | market-data-processing-service   | trading-analytics                                            |

**Gap:** No API service owns the **position + risk** domain. Position monitor (reconciled positions) and risk metrics are either:

- Accessed directly from UIs (violates convention), or
- Proxied through ERA (wrong domain — ERA is trade-centric, not position-centric)

---

## 3. Proposed: position-and-risk-api (PRA)

### Purpose

A new API service at L10 that:

- Proxies **position monitor** (reconciled positions SSOT)
- Proxies **risk-and-exposure-service** (when built)
- Aggregates position, PnL, margin, and risk views for UIs

### Suggested UIs to Route Through PRA

| UI                   | Primary Data                 | Notes                                         |
| -------------------- | ---------------------------- | --------------------------------------------- |
| settlement-ui        | Positions, invoices, T+1     | Settlement reports, cash flows, fee breakdown |
| strategy-ui          | Positions, risk metrics      | Live positions, strategy PnL                  |
| pnl-attribution-ui   | PnL breakdown by dimension   | Could stay CRA or move — see DRY below        |
| risk-and-exposure-ui | VaR, Greeks, circuit breaker | When built                                    |

### Port Suggestion

- **8005** — next available in the L10 API cluster

---

## 4. DRY with client-reporting-api

**client-reporting-api** (CRA) serves client-facing reports: PnL, portfolio summaries, custom exports. **position-and-risk-api** would serve internal/ops views: positions, risk, settlement.

**Shared concerns (avoid duplication):**

1. **Report generation pipeline** — PDF/CSV export, templating
2. **Auth middleware** — CRA has per-client JWT; PRA may need per-strategy or per-role
3. **Aggregation patterns** — time-range queries, dimension rollups

**Options:**

- **A) Shared library:** Extract unified-reporting-interface or extend unified-trading-library with report-generation primitives; both CRA and PRA import it
- **B) PRA as CRA extension:** Add position/risk routes to CRA — but CRA is client-facing, PRA is internal; different auth and SLAs
- **C) Separate repos, shared patterns:** PRA and CRA stay separate; document shared patterns in codex; implement once in each, refactor to shared lib when duplication becomes painful

**Recommendation:** Start with **C**; extract shared lib when we have 2+ concrete implementations. Avoid over-engineering before both APIs exist.

---

## 5. Suggested PRA Structure

position-and-risk-api/
api/
main.py
routes/
positions.py # GET /positions, /positions/{client_id}, /positions/summary
risk.py # GET /risk/metrics, /risk/var, /risk/greeks (when risk service exists)
settlement.py # GET /settlement/invoices, /settlement/cash-flows, /settlement/t+1
health.py
clients/
position_service.py # HTTP client to position-monitor or position-service
models/
schemas.py # Pydantic models for positions, risk, settlement
tests/
cloudbuild.yaml
pyproject.toml

**Key routes (draft):**

| Route                      | Source                    | Purpose                          |
| -------------------------- | ------------------------- | -------------------------------- |
| GET /positions             | position monitor          | All reconciled positions         |
| GET /positions/summary     | position monitor          | Aggregated by client/strategy    |
| GET /settlement/invoices   | TBD (settlement service?) | Invoice list and detail          |
| GET /settlement/cash-flows | TBD                       | Cash flow view                   |
| GET /risk/metrics          | risk-and-exposure-service | VaR, Greeks, margin (when built) |

---

## 6. Interim: settlement-ui to execution-results-api

Until PRA exists, **settlement-ui** will route to **execution-results-api** (8002). This is a **temporary workaround**:

- ERA has execution records that can be used for basic settlement views
- Not ideal — ERA is trade-centric, not position-centric
- Document this as technical debt; migration path: settlement-ui to PRA when PRA is built

---

## 7. Codex Updates Needed

1. **api-services-cluster.md** — Add PRA to cluster; clarify ERA = trade analytics, PRA = position/risk
2. **UI-DEPENDENCY-MATRIX.md** — Update settlement-ui, strategy-ui to PRA (when built); note interim ERA routing
3. **New doc or section** — "API Service Convention: Services Do Not Directly Serve UIs"
   - Rule: UIs consume backend APIs; APIs aggregate from one or many services
   - Naming: _-api = L10 HTTP boundary; _-service = L7/L9 engine
   - Responsibilities: auth, typed contracts, aggregation, rate limiting

---

## 8. Open Questions for Discussion

1. Does position monitor live as a separate service, or inside execution-service / another engine?
2. Where does settlement data (invoices, cash flows, T+1) originate? New settlement-service or extension of existing?
3. Should strategy-ui move from ERA to PRA immediately when PRA exists, or phased?
4. CRA vs PRA auth: CRA has per-client JWT; PRA — internal only (no auth) or per-role?

---

## 9. Next Steps

- [ ] Socialize this plan with team
- [ ] Decide on PRA scope and timeline
- [ ] Update codex with API service convention
- [ ] Add settlement-ui interim routing note to UI-DEPENDENCY-MATRIX
- [ ] Create PRA repo when approved
