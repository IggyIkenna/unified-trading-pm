---
doc_type: plan
title: tradfi satellite AO dispatch batch 17 — 2026-08-18
summary: >-
  Extraction batch from the tradfi tranche's 2026-08-18 /na-eligibility-audit sweep (dispatch agt-31bfcb) —
  per-todo split path: 2 conflict-cleared, bounded/deterministic items pulled from 2 brand-new (2026-08-18)
  tradfi/cross-cutting issue docs whose remaining todos are otherwise genuinely operator/design-gated
  (features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md,
  features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md). Conflict-checked against every active
  tradfi satellite batch (9/9-2/12/13/15/16) and tradfi_consolidated_closeout_2026_07_18.md — zero hits on either
  source doc's basename, no existing coverage.
status: active
nature: process
asset_group: [tradfi]
stage: [features]
repos: [features-service]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-batch, na-eligibility-audit, features-service, compliance]
related:
  [
    /plans/archive/2026_08/issues/features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md,
    /plans/active/issues/features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/issues/features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md,
    /plans/active/issues/features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  na-eligibility-audit, tradfi tranche, dispatch agt-31bfcb, 2026-08-18 — per-todo split extraction of the bounded
  slice from 2 brand-new issue docs, each a mix of bounded and genuinely operator/design-gated items.
resolved_by:
---

# TradFi satellite AO dispatch batch 17 — 2026-08-18

Extracted via `/na-eligibility-audit tradfi`'s per-todo split path (2026-08-18): 2 brand-new tradfi issue docs each
carry a mix of bounded and genuinely operator/design-gated todos. The bounded slice is dispatched here; each source
doc stays `assigned_vm: NA` for its remaining gated items (see each source doc's own Progress Log for the split
rationale).

## Todos

- [x] ✅ [REVIEW] P1. **Confirm current blast radius of the banned-vendor `corporate_actions` calculator** — is
      `features_service/calendar/cli/handlers/corporate_actions_handler.py`'s CLI (`--operation corporate_actions
      --mode batch`) actually invoked by a scheduled/production job today, or built-but-never-run? Check Cloud
      Scheduler / cron / any orchestrator config that could dispatch this operation (the sibling `earnings_results`
      leg of the SAME handler is confirmed genuinely dispatched — this todo answers the question only for the
      Polygon.io-sourced `corporate_actions` leg specifically). Worker-determinable: this is a factual investigation
      (is it wired to a live schedule, yes/no), not a judgment call. Done when: a definitive answer is recorded
      (scheduled + evidence, or confirmed dead/unscheduled) in the source doc's Progress Log. Source:
      `features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md` todo 1 (`[REVIEW] P1`).
      ✅ 2026-08-19: **CONFIRMED UNSCHEDULED (built-but-never-run)** — `--operation corporate_actions --mode batch` is
      registered/callable (features-service@afa03168) but no Cloud Scheduler / cron / orchestrator config dispatches it
      today; full evidence in the source doc's Progress Log.
- [ ] [DOC] P3. **Add a one-line note to `batch_handler.py` on why the calendar domain has no distinct paper mode**
      — read `batch_handler.py`/`live_handler.py` (features-service calendar CLI) to confirm whether paper reuses
      batch output directly (calendar events are exogenous/scheduled, same fact regardless of trading mode) or
      paper mode was genuinely never built, then state which in a one-line docstring/comment note. Worker-
      determinable: read the code, confirm the fact, document it — no design decision needed. Done when: the note
      is added and cites which case applies. Source:
      `features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md` todo 3 (`[DOC] P3`).

## Progress Log

- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): drafted, conflict-cleared (grepped
  every active tradfi satellite batch + `tradfi_consolidated_closeout_2026_07_18.md` for both source docs'
  basenames — zero hits, no existing coverage claims this ground), and activated directly (`status: active`, not
  `draft` — `/na-eligibility-audit` is authorized to apply verdicts, unlike `/ag-closeout-audit`'s read-only
  batches). The remaining todos on both source docs (operator vendor-resourcing decision, contingent registry
  declaration, Layer-1-EXPECTED-universe design question, contingent `record_captured` wiring) stay genuinely
  gated — see each source doc's own Progress Log.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
