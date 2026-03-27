# Unknowns Questionnaire (Pre-Implementation Gate)

Use this questionnaire before writing implementation tasks. If unresolved answers remain in critical sections, do not
advance beyond planning.

---

## 1) Live Decomposition + Exchange Interface

- Which responsibilities belong in an `exchange-interface` package vs execution service?
- What are the required adapter methods for all venues?
- What are retry/idempotency/order guarantees per venue?
- Which failures trigger circuit break vs degraded operation?

Locked decision:

- Boundary is thin adapter (venue IO + normalization + retry/idempotency only).
- MVP adapter contract includes:
  - market data stream subscribe/unsubscribe
  - order place/cancel/amend
  - order status and fill events
  - reconnect and health hooks
- Execution manager keeps order state and internal position tracking for its own fills/trades to compare against
  position monitor.

## 2) Risk Stack Separation

- Which service owns canonical position/account truth?
- Which service computes exposure, and at what latency target?
- Which service computes risk limits, and which limits are blocking?
- Which service computes attribution, and which consumers depend on it?
- How are cross-service contracts versioned without cycles?

Locked decisions:

- Execution owns order/trade truth.
- Position/account monitor owns canonical final position truth.
- MVP risk posture is warn-then-block, with single on-call override and audit log.
- Hard-block set includes:
  - max position/notional breach
  - max drawdown breach
  - exchange connectivity loss on active strategy
  - critical reconciliation break
  - stale market data feed
  - manual kill switch
- Exposure model supports strategy-level and account-level views, including cross-venue rollups.
- Exposure storage model uses separate materialized views for strategy-level and account-level netting.
- Reconciliation supports auto-reconciliation at any mismatch size with strong safety testing and operator visibility.
- Reconciliation response baseline:
  - <2% notional mismatch: background auto-reconciliation
  - 2% to <10% notional mismatch: background auto-reconciliation + priority refresh signal
  - > =10% notional mismatch: immediate consumer refresh/re-sync expectation

## 3) Options/Futures Attribution and Execution

- What is the canonical model for multi-leg representation?
- Which pricing and greeks conventions are mandatory?
- How do we decompose basis/carry/funding rates for futures/perps?
- How are settlement and expiry events represented?
- What sign conventions and base-currency normalization rules are used?

Locked decision:

- Use dual-base output (USD and native currency fields).
- Use uniform sign convention: positive is gain/profit, negative is loss.
- Residual policy baseline is tight (exact thresholds still to be finalized).
- Threshold profile is per-asset configurable (tighter options/futures, looser spot/staking).

## 4) Alerting and Observability Contract

- Which lifecycle events are mandatory for all services?
- Which metrics are required for readiness vs optional?
- What severity matrix routes to log-only, Slack, or PagerDuty?
- How is live alerting validated safely on non-production keys?
- What evidence is required for UAT acceptance of observability?

Locked decision:

- Default severity routing is critical->PagerDuty, warning->Slack, info->log-only.
- Non-prod alert test policy is daily synthetic heartbeat plus weekly failure-injection.

## 5) Dual-Cloud Success Criteria

- Which pass/fail gates must exist in deployment checklist YAMLs?
- Which services are cloud-portable now vs deferred with waiver?
- Which abstractions must be complete (storage, secrets, messaging)?
- What DR RTO/RPO targets are required by service tier?
- How are cloud-readiness statuses synced into GitHub fields/subtasks?

Locked decision:

- All new services in Wave 1 must be cloud-portable.
- Tier-1 DR baseline target: RTO<=30m and RPO<=15m.
- Portability gate depth is API/artifact parity + deployability proof (runtime validation on primary).

## 6) Security and Auth

- What is the exact Okta SSO scope for this wave?
- What token model is used for service-to-service auth?
- What is the least-privilege matrix by environment?
- What network hardening policy applies to all services?
- Which vulnerabilities and dependency issues are blocking gates?

Locked decision:

- Okta SSO applies to all operator/internal UIs in Wave 1.
- Internal service traffic remains inside GCP VPC boundary in Wave 1 with IP hardening on external usage.
- MVP role model is Admin/Operator/Viewer/ClientViewer/ClientAnalyst.
- Operator UI MVP includes: health/release status, rollback controls, alert panel+ack, PnL drilldown, model promotion
  controls, tenant onboarding admin.
- Phase-1 service auth baseline is fixed to VPC-internal + least-privilege service accounts (no heavier auth model in
  this phase).
- Dev/prod component delivery follows packaging parity and avoids source exposure (image/package consumption model).

## 7) Hive-Compatible Schema Refactor

- Which datasets migrate first?
- What backward compatibility strategy is used (dual-write/migration window)?
- What schema evolution and partition rules are mandatory?
- What contract tests prevent downstream breakage?
- How is lineage/version exposed in observability and reporting?

## 8) Commercial Milestone Operationalization

- What qualifies as ML signal commercialization?
- What qualifies as end-to-end strategy commercialization?
- How do CEFI/TRADFI and DeFi commercialization gates differ?
- What PM artifacts are auto-created at each stage?
- What approvals are required to advance stage?

Locked decision:

- Use two-tier ML commercialization:
  - preliminary commercialization at paper stage,
  - full commercialization after live evidence window.
- ML promotion approval chain for MVP is single owner approval with audit logging.
- ML metadata source-of-truth baseline is GCS manifest + BigQuery index.
