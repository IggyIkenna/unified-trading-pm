---
title: "AUDIT-03 — Phase 0 design-review findings"
audit_id: AUDIT-03
run_phase: "Phase 0 — design review (codex + plans read; NO code-run yet)"
date: 2026-05-21
auditor: Harsh + Claude Opus 4.7 (1M)
checklist: audits/audit-files/audit_03_defi_archetypes_e2e.md
flow_ref: audits/audit-files/defi_strategy_e2e_flow.md
scope: e2e flow walkthrough — onboarding + reporting bookends; design≠code divergences surfaced while agreeing the flow
---

# AUDIT-03 — Phase 0 design-review findings (2026-05-21)

Surfaced while agreeing the e2e flow (`defi_strategy_e2e_flow.md`). These are **design-vs-code divergences read from
codex + plans** — not yet confirmed by running code. Each is confirmed/killed when its checkpoint is walked (Phase 1
READ). No live data used; no synthetic injection.

## New findings

| ID   | Checkpoint | Class       | Finding                                                                                                                              | Evidence                                         | Recommended action                                                         | Sev | Status |
| ---- | ---------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------ | -------------------------------------------------------------------------- | --- | ------ |
| F-01 | RPT-03     | CODE-DRIFT  | DART 3-way batch/paper/live comparison is mock-only; real backend endpoint host undecided                                            | `dart/mode-toggle.md`; pvl-p23b TBD              | Decide endpoint host (deployment-api vs strategy-service) + wire real data | P0  | OPEN   |
| F-02 | RPT-04     | CODE-DRIFT  | `ManualTradeGateDialog` is design-spec only — not wired to a real backend; gates first 3 trading days                                | pvl-p23c; promote plan U5/U6                     | Implement + wire approve→`MANUAL_APPROVED`→execution unhold                | P0  | OPEN   |
| F-03 | RPT-05     | CODE-DRIFT  | Strategy-audit GCS writer not wired — strategy events land only in events JSONL; `audit/{client_id}/…strategy.json` is design-intent | `audit-logging.md`; slot-8 PB-4                  | Wire strategy-audit GCS writer                                             | P1  | OPEN   |
| F-04 | RPT-06     | CODE-DRIFT  | Execution-audit path keyed by `client_order_id` not `client_id`                                                                      | `audit-logging.md` PB-3                          | Align audit path key                                                       | P1  | OPEN   |
| F-05 | RPT-08     | GAP         | Audit bucket lacks GCS Object Versioning + Retention Lock (immutability by construction only)                                        | slot-8 PB-2/PB-8                                 | Provision versioning + retention lock                                      | P1  | OPEN   |
| F-06 | ONB-07     | CODEX-DRIFT | Entity-model doc conflict: CLAUDE.md "Odum UK + Cayman boundary" vs onboarding codex "Elysium (Ireland) → POD → BVI Fund"            | CLAUDE.md multi-client §; `client-onboarding.md` | Reconcile — one is stale; fix the wrong doc                                | P1  | OPEN   |

## Already tracked (do NOT dual-track — listed for completeness)

| Item                                         | Tracked as     | Where                      |
| -------------------------------------------- | -------------- | -------------------------- |
| Engines hand-build legs (no `LegController`) | KD-01          | audit doc §3               |
| CEFFU custody stub (`NotImplementedError`)   | KD-07          | audit doc §3 (June-1 flip) |
| `usdc_idle_yield_apy_bps` unwired → 0        | KD-02 / GAP-01 | audit doc §3 / §4          |
| ASTER `derivative_ticker` missing            | GAP-04         | audit doc §4               |
| per-account `health_factor` not sourced      | GAP-08         | audit doc §4               |

## Next

Each F-NN gets confirmed/killed when its RPT-_/ONB-_ checkpoint is walked (Phase 1 READ). On confirmation → todo in the
relevant active plan — reporting findings likely land in `client_reporting_pnl_attribution_mvp_2026_05_10.md` +
`promote_workflow_may23_cli_path_2026_05_10.md`; entity-model (F-06) is a CLAUDE.md ↔ codex reconcile. Per CLAUDE.md
commit-and-flip discipline.
