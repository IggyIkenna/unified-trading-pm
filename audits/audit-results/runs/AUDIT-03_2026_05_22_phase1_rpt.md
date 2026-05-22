---
title: "AUDIT-03 — Phase 1 READ results: §2.12 RPT (reporting / audit surface)"
audit_id: AUDIT-03
run_phase: "Phase 1 — static drift, READ checkpoints; re-confirm Phase-0 findings F-01..F-05"
section: "§2.12 reporting / audit surface (RPT-*)"
date: 2026-05-22
method: "sonnet sub-agent first-pass (evidence-required) → Opus reviewer consolidation"
auditor: Harsh + Claude Opus 4.7 (reviewer)
checklist: audits/audit-files/audit_03_defi_archetypes_e2e.md
code_audited:
  - client-reporting-api — api/routes/{attribution,pnl}.py, core/attribution_reader.py
  - deployment-ui — src/components/ClientReportingTab.tsx
  - unified-trading-system-ui — components/dart/{dart-three-way-view,manual-trade-gate-dialog}.tsx, lib/api/dart-client
  - strategy-service@b303a358 — signal_broadcast/audit.py
  - execution-service@a848ef61 — utils/audit_log.py, pnl_attribution/rows.py
  - unified-trading-library — event_sink.py
oracle:
  codex/04-architecture/client-reporting-architecture.md + codex/14-customer-journeys/dart/mode-toggle.md +
  codex/07-security/audit-logging.md + codex/05-infrastructure/live-deployment-monitoring.md
---

# AUDIT-03 — Phase 1 READ — §2.12 RPT

Sub-agent first pass, Opus-reviewed. **Key result: F-01 and F-02 are REFUTED** (DART 3-way + ManualTradeGateDialog are
now wired to real backends — they were design-only at the 2026-05-21 Phase-0 review). F-03/F-05 CONFIRMED; F-04
partially refuted; **2 new findings (F-45 RPT-07, F-46 RPT-09)**.

## Per-checkpoint verdicts

| ID     | Verdict                                 | Evidence                                                                                                                                                                                                                                                                                                                                                       |
| ------ | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RPT-01 | PASS                                    | `client-reporting-api/.../routes/attribution.py:230,245,260,274` serves `/nav`,`/pnl`,`/positions`,`/attribution`; live reads via `read_attribution_rows()` (attribution_reader.py:36); bucket via `resolve_bucket_name(kind="client-reports")` (51, SSOT-compliant). Minor: a duplicate `/pnl?client_id=` route exists in routes/pnl.py                       |
| RPT-02 | PASS                                    | `deployment-ui/.../ClientReportingTab.tsx` renders Nav/PnL/Attribution charts + Drilldown/Positions/Hwm tables, wired to `/api/v1/clients/{id}/...`; drilldown columns match codex (date/strategy/instrument/factor/layer/amount/venue). `/positions` returns mock (MVP placeholder, code-commented)                                                           |
| RPT-03 | PASS — **REFUTES F-01**                 | `unified-trading-system-ui/.../dart-three-way-view.tsx` imports `fetchStrategyRuns` from `@/lib/api/dart-client` (real backend), `MODES=["batch","paper","live"]`, polls 30s. F-01 ("mock-only, backend TBD") no longer holds                                                                                                                                  |
| RPT-04 | PASS — **REFUTES F-02**                 | `manual-trade-gate-dialog.tsx` polls `listPendingInstructions` (1s); `handleApprove`→`approveInstruction`→`POST .../approve`; `handleReject`→`POST .../reject`; renders risk preview (margin_usd/position_limit_pct/worst_case_loss_usd). All wired via `@/lib/api/dart-client`. F-02 ("design-only") no longer holds                                          |
| RPT-05 | CODE-DRIFT — **CONFIRMS F-03**          | `strategy-service/.../signal_broadcast/audit.py` `EmissionAuditor` only `log_event(STRATEGY_SIGNAL_*)` → events JSONL; no `persist_audit_log` GCS strategy-audit writer. Codex audit-logging.md:148 acknowledges this as PRE_CUTOVER (slot 8 PB-4)                                                                                                             |
| RPT-06 | CODE-DRIFT — **PARTIALLY REFUTES F-04** | `execution-service/.../utils/audit_log.py:67` path now `audit/{client_id}/{YYYY-MM-DD}/{event_type}/{order_id}_{ts}.jsonl` — top-level is `client_id` (refutes F-04's "keyed by client_order_id"). BUT 3 residual shape divergences vs codex: date `YYYY-MM-DD` vs `YYYY/MM/DD`; ext `.jsonl` vs `.json`; `/{event_type}/` dir vs `{ts}-{event_type}` filename |
| RPT-07 | **CODE-DRIFT**                          | `unified-trading-library/.../event_sink.py:129-131` writes `events/{service}/{date}/{instance_id}/hour={HH}/...` — 3rd segment is `instance_id` (VM_NAME or host-pid); codex live-deployment-monitoring.md:38 specifies `correlation_id`. 11 lifecycle events confirmed. Prefix-filtering by correlation_id impossible → **F-45**                              |
| RPT-08 | GAP — **CONFIRMS F-05**                 | Codex audit-logging.md Retention-Lock `last_executed: NEVER`; no terraform/script/manual step provisions GCS Object Versioning + Retention Lock for audit/event buckets (PRE_CUTOVER, routed to slot 4)                                                                                                                                                        |
| RPT-09 | **CODE-DRIFT**                          | `execution-service/.../pnl_attribution/rows.py:62` `FillAttributionContext.archetype_id: str                                                                                                                                                                                                                                                                   | None = None`(optional); codex`PnLAttributionRow`spec =`archetype_id: str`(required). Rows could emit`archetype_id=None`→ unqueryable per-archetype. No`config_variant` field anywhere → **F-46**. Composes PNL-13 |

## Findings

| ID     | Checkpoint | Class      | Finding                                                                                                                                                                                                                                                                  | Sev                                                                                                                                                          | Maps-to | Status     |
| ------ | ---------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------- | ---------- | --------- |
| (F-01) | RPT-03     | —          | **REFUTED** — DART 3-way is wired to a real backend (`dart-client.fetchStrategyRuns`), not mock                                                                                                                                                                          | —                                                                                                                                                            | F-01    | RESOLVED   |
| (F-02) | RPT-04     | —          | **REFUTED** — ManualTradeGateDialog fully wired (poll + approve/reject → POST), risk preview rendered                                                                                                                                                                    | —                                                                                                                                                            | F-02    | RESOLVED   |
| (F-03) | RPT-05     | CODE-DRIFT | **CONFIRMED** — strategy audit emits events-JSONL only; no GCS strategy-audit writer (`persist_audit_log` equivalent). Acked PRE_CUTOVER (slot 8 PB-4)                                                                                                                   | P1                                                                                                                                                           | F-03    | CONFIRMED  |
| (F-04) | RPT-06     | CODE-DRIFT | **PARTIALLY REFUTED** — path now `client_id`-keyed (was `client_order_id`); 3 residual shape divergences (date sep / extension / event_type segment) vs codex                                                                                                            | P2                                                                                                                                                           | F-04    | DOWNGRADED |
| (F-05) | RPT-08     | GAP        | **CONFIRMED** — audit/event bucket GCS Object Versioning + Retention Lock never provisioned                                                                                                                                                                              | P1                                                                                                                                                           | F-05    | CONFIRMED  |
| F-45   | RPT-07     | CODE-DRIFT | `GcsEventSink` path 3rd segment is `instance_id` not `correlation_id` (event_sink.py:129-131) vs codex live-deployment-monitoring.md:38 — correlation_id prefix-filtering impossible. Likely codex stale post-2026-05-01 rev (reviewer: confirm which side is canonical) | P1                                                                                                                                                           | new     | CONFIRMED  |
| F-46   | RPT-09     | CODE-DRIFT | `FillAttributionContext.archetype_id` is `str                                                                                                                                                                                                                            | None`(optional) vs codex required`str`; could emit `None`→ unqueryable per-archetype attribution rows. No`config_variant` field. rows.py:62. Composes PNL-13 | P1      | new        | CONFIRMED |

## Reviewer notes

- **F-01/F-02 refutation is the headline**: both Phase-0 DART/manual-gate findings have since been implemented (real
  backend wiring via `@/lib/api/dart-client`). The §6 findings index should mark F-01/F-02 RESOLVED. This also de-risks
  CUT-03 (the dialog exists + is wired) — the residual CUT-03 gap (F-44) is only the missing Playwright e2e for the
  approve/deny/timeout flow.
- **F-45 (correlation_id vs instance_id)** needs an Opus/operator call on which side is canonical: the `GcsEventSink`
  docstring describes the instance_id layout as a deliberate 2026-05-01 redesign (rate-limit fix on the cefi audit). If
  so, codex live-deployment-monitoring.md:38 is the stale side (→ CODEX-DRIFT, fix the doc) rather than the code.
- **F-46 (archetype_id optional)**: codex is the oracle (`archetype_id: str` required). Before tightening the field,
  grep all `FillAttributionContext(` construction sites — any without `archetype_id` would break. Composes
  PNL-13/RPT-09.
- **F-04 downgraded P0→P2**: the security-critical part (per-client keying) is now correct; the residual is cosmetic
  path shape (date sep / extension / segment order) — reconcile codex↔code, low risk.
