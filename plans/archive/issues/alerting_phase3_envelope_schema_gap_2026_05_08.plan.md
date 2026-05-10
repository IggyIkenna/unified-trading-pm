---
title: "Alerting Phase 3 producer migration — UAC envelope schema gap (RESOLVED)"
created: 2026-05-08
author: agent-5-tab5-orchestrator (recreated; original by sub-agent B)
source:
  - unified-api-contracts/unified_api_contracts/internal/alerting/__init__.py
  - unified-api-contracts/unified_api_contracts/internal/alerting/alerts.py
  - unified-api-contracts/unified_api_contracts/internal/risk.py
  - plans/active/alerting_service_live_rules_2026_05_07.md § "Phase 3 — Producer migration"
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# ✅ RESOLVED 2026-05-08 — Operator chose Option A; envelope extension shipped

> **Severity**: P0 — was blocking Phase 3 producer migration. **Status**: ✅ RESOLVED. **Resolution**: operator chose
> Option A (extend envelopes with `code: AlertCode`); shipped end-to-end via UAC@2636815
>
> - execution-service@624c36a8 + position-balance-monitor@d206ab3 + risk-and-exposure@915f0de.

## Original finding (Sub-Agent B, 2026-05-08 mid-cycle)

The 3 active UAC alert envelope models had **no `code: AlertCode` field** — Phase 3 producer migration of
risk-and-exposure-service / position-balance-monitor-service / execution-service / features-onchain-service from raw
strings → `AlertCode` enum was blocked because the envelopes carrying the codes had no slot for them:

- `AlertEvent` (`internal/alerting/__init__.py`) — used by execution-service yield_recon + funding_recon, PBM
  reconciliation_engine + fee_reconciliation_engine. No code field.
- `AlertMessage` (`internal/risk.py`) — used by R&E `alert_manager.py`. Used legacy `AlertType` enum.
- `DefiAlert` (`internal/alerting/alerts.py`) — used legacy `DefiAlertType` enum.

Three architectural options surfaced (extend envelopes / use details dict / deprecate legacy enums); operator-class
design judgment, not sub-agent mechanical work.

## Resolution chain

| Step                                          | Commit                                   | Description                                                                                                                                |
| --------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Operator decision                             | (chat 2026-05-08)                        | Choose **Option A** — extend the 3 envelopes with `code: AlertCode`                                                                        |
| UAC envelope extension (Wave 1)               | UAC@2636815                              | `code: AlertCode \| None = None` field on AlertEvent + AlertMessage + DefiAlert; lazy-import resolution; backward-compat with legacy enums |
| execution-service consumer migration (Wave 2) | execution-service@624c36a8               | yield_recon + funding_recon AlertEvents stamped with AlertCode                                                                             |
| position-balance-monitor consumer migration   | position-balance-monitor-service@d206ab3 | reconciliation_engine + fee_reconciliation_engine AlertEvents stamped with AlertCode                                                       |
| risk-and-exposure consumer migration          | risk-and-exposure-service@915f0de        | RiskMonitor.\_send_alert AlertMessage emissions stamped with AlertCode                                                                     |
| KillSwitchScope field on AlertRule (Wave 3+)  | UAC@3793310 + UAC@2541a47                | + alerting-service@8eda37c (publisher hook + integration test consuming `code: AlertCode` from emitted events)                             |

## What's deferred (non-blocking)

- features-onchain-service emission sites — DEFERRED per Sub-B finding: the 5 DEFI\_\* codes target calculators that
  aren't yet wired (defi_master Fork 1 territory). Emission sites materialise as part of carry_staked_basis live wiring.
- Producer migration unit tests per service — captured as alerting-plan Phase 3 todos; ship as part of each service's
  next test sweep.

## Composes with

- `alerting_service_live_rules_2026_05_07.md` Phase 3 producer migration — unblocked.
- `master_to_live_defi_2026_05_23.md` Group F item 22 (alerting wiring) — partial credit pending features-onchain
  emission sites.
