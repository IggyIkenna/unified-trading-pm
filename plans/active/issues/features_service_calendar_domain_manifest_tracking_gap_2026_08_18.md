---
doc_type: issue
title: features-service calendar domain (economic_events, forexfactory, corporate_actions, earnings_results) writes outside the honest-coverage manifest
summary: >-
  The whole `calendar/` feature family (economic_events, economic_results, yield_curve, forexfactory,
  corporate_actions, earnings_results) writes to its own path convention (`calendar/{feature_type}/by_date-or-week/
  {date}/{file}.parquet`, documented per-handler) but none of it calls `record_captured` or otherwise registers with
  the honest-coverage manifest/capture_status system — coverage.json has zero visibility into whether this data is
  actually being captured, how completely, or when it last ran.
status: open
nature: process
asset_group: [tradfi] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [tradfi, cross-cutting]; macro/calendar data is tradfi-only per the corpus's own prior cross-cutting audit precedent, not multi-AG
stage: [features]
repos: [features-service]
scope: [engineer]
tags: [honest-coverage, manifest, calendar, features-service, data-pipeline-correctness]
priority: P2
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
created: 2026-08-18
source: >-
  Found answering an operator question about how the calendar domain's batch/paper/live read path is tracked, during
  the same EVENT_DRIVEN archetype registry investigation as the sibling Polygon.io finding
  (features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md). Confirmed by direct read of
  corporate_actions_handler.py, economic_results_handler.py, forexfactory_handler.py, and batch_handler.py — no
  `record_captured` (or equivalent) call found in any of them.
related:
  [
    /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
  ]
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    features-service/features_service/calendar/engine/calendar_orchestrator.py,
    features-service/features_service/calendar/cli/handlers/corporate_actions_handler.py,
    market-tick-data-service/market_tick_data_service/live/manifest_recorder.py,
  ]
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
drift_direction: advance-code
depends_on: []
archive_exempt: true # 0-open-todos 2026-08-21 (both todos resolved same session) — full 6-step archival (8 corpus
  # referrers to repoint) deferred to a dedicated hygiene pass, tracked as a real todo in the T3 plan's Close-out
  # section rather than left prose. Intentional bridge, not a permanent exemption.
---

# features-service calendar domain writes outside the honest-coverage manifest

## What was found

Every calendar-domain handler documents a real, consistent GCS write path in its own module docstring:

- `calendar/economic_results/by_date/day={YYYY-MM-DD}/macro_results.parquet`
- `calendar/forexfactory/by_week/week={YYYY-MM-DD}/macro_results.parquet` (weekly grain — the one outlier;
  everything else is daily)
- `calendar/corporate_actions/by_date/day={YYYY-MM-DD}/{dividends,splits}.parquet`
- `calendar/earnings_results/by_date/day={YYYY-MM-DD}/results.parquet`

None of these paths follow the standard MTDS hive layout (`asset_group=X/venue=Y/instrument_type=Z/data_type=W/`)
that the honest-coverage manifest/capture_status system is built around — this is a deliberately different,
calendar-specific convention. That in itself may be fine (calendar data doesn't cleanly fit the venue/instrument_type
axes), but no handler in this family calls `record_captured` (or any equivalent manifest-write function) — checked
directly across `corporate_actions_handler.py`, `economic_results_handler.py`, and `forexfactory_handler.py`. This
means:

- `coverage.json` / the honest-coverage dump have zero rows for any calendar data_type — not `expected_unattempted`,
  not `attempted_failed`, nothing. The whole domain is invisible to the standard coverage measurement this codebase
  otherwise treats as load-bearing (CLAUDE.md: "Data pipeline correctness is the heartbeat").
- There is no machine-checkable way to answer "did today's economic-calendar batch run, and did it write real
  rows" without manually reading GCS or the service's own logs.

## Mode coverage, a related but distinct observation

The calendar CLI's `batch_handler.py` only declares `choices=["batch", "live", "info"]` — no distinct `paper` mode.
`live_handler.py` streams via Pub/Sub (`get_messaging_protocol(mode="live") -> "pubsub"`). Calendar events are
exogenous/scheduled (the same NFP release date is the same fact regardless of trading mode), so paper likely reusing
batch-computed data directly is a reasonable design — but it's not stated anywhere as a deliberate choice, which is
worth a one-line doc note distinguishing "no paper mode because it's unnecessary here" from "paper mode was never
built."

## Why this wasn't fixed in the same commit

This is a real gap across an entire feature domain, not a bounded edit — wiring `record_captured` into 4+ handlers,
choosing what "shard" even means for a weekly-grain forexfactory write vs. a daily one, and deciding whether
Layer-1's EXPECTED universe should include calendar data_types at all, are each real design questions. Filed rather
than silently worked around, per findings-triage (outside every currently-open plan).

## Todos

- [x] ✅ [REVIEW] P2. **RULED 2026-08-20 (operator, T3 session): YES, calendar belongs in Layer-1.** The
      event-driven shape doesn't disqualify it; the shard-atom is `feature_group` (the calendar sub-domain name)
      + `feature_family="calendar"`, not per-venue-per-instrument.
- [x] ✅ [AGENT] P2. **SHIPPED 2026-08-21, `features-service@b2851c442e`.** Re-verified against current code
      (this doc's original "checked directly, no handler has it" claim was stale by the time of this pass):
      `economic_results_handler.py`, `forexfactory_handler.py`, and `calendar_orchestrator.py` ALREADY had this
      wiring (landed independently, sometime after 2026-08-18, without this doc being updated). Only
      `corporate_actions_handler.py` was actually missing it — fixed, mirroring the siblings' exact pattern.
- [x] ✅ [DOC] P3. **EXTRACTED 2026-08-18 (na-eligibility-audit, tradfi tranche, dispatch agt-31bfcb) →
      `tradfi_satellite_ao_dispatch_batch17_2026_08_18.md` todo 2.** Add a one-line note to `batch_handler.py` on
      why calendar has no distinct paper mode (reuses batch output directly, or is genuinely unbuilt — state which,
      once confirmed). Bounded, worker-determinable (read the code, confirm the fact, document it) — dispatched
      separately from todos 1/2 above, which stay genuinely design/contingent-gated.

## Progress Log

**2026-08-18 — filed.** Found answering an operator question, not from a dedicated audit — narrow, direct-read
confirmation across 4 handler files, not a corpus-wide sweep of every features-service domain.
- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): **RECLASSIFY, per-todo split.** Todo 3
  (paper-mode doc note) is bounded/worker-determinable — extracted to
  `tradfi_satellite_ao_dispatch_batch17_2026_08_18.md` todo 2 (conflict-cleared, zero existing coverage). Todo 1
  (Layer-1 EXPECTED-universe design question) and todo 2 (contingent `record_captured` wiring, gated on todo 1)
  stay genuinely design/contingent-gated. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-19** (tradfi tranche, dispatch agt-5d34f9): **KEEP-NA, valid — reaffirmed.** 2 open
  todos re-read end-to-end (count reconciled, 2/2), unchanged since the 08-18 pass. Todo 1 (Layer-1 EXPECTED-universe
  design question) is a genuine architectural judgment call; todo 2 is textually gated on todo 1's unresolved
  outcome. `assigned_vm` unchanged.
- **context-scout 2026-08-19**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed. Both open todos (the Layer-1 EXPECTED-universe
  design question and its contingent `record_captured` wiring) remain genuine architectural judgment work, unchanged
  since the 08-19 pass. `assigned_vm` unchanged.
- **2026-08-21 (T3 session)**: ruling landed + wiring shipped in the same session (race with the audit pass above —
  harmless, both landed). Todo 1 ruled YES; todo 2 shipped `features-service@b2851c442e` — 3 of 4 handlers turned
  out to already have this wiring (landed independently after 2026-08-18, this doc never updated to reflect it),
  only `corporate_actions_handler.py` genuinely needed the fix. Zero open todos remain in this doc; leaving
  `status: open` for a follow-on archival pass rather than doing the full 6-step archive ritual inline here.
