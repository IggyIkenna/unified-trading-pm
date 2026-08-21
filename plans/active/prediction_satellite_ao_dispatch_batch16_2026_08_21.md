---
doc_type: plan
title: prediction satellite AO dispatch batch 16 — 2026-08-21
summary: >-
  Extraction batch from the prediction tranche's 2026-08-21 /ag-closeout-audit Phase 3 pass (re-verifying the
  2026-08-21 Phase-1 parked doc's 7-row orphan table) — 3 conflict-cleared, bounded, UNGATED items pulled from
  ONE source doc: `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md`
  (all 3 of that doc's open todos; the doc has been re-confirmed KEEP-NA by 6 consecutive na-eligibility-audit
  passes 2026-08-14→2026-08-21 on the grounds its 3 items "redirect" to `cross_ag_live_capture_parity_2026_08_14.md`
  — but that redirect target is itself `assigned_vm: NA` / `execution_scope: local-only` (a human/local plan, not
  AO-dispatched), so the redirect is a mutual pointer between two NA docs and nobody is actually dispatched to do
  the underlying fix. This batch breaks that stalemate by extracting the 3 concrete, bounded fixes directly.
  `status: draft` — a skill-drafted AO batch is never auto-shipped; flipping to `active` to dispatch is an operator
  decision (CLAUDE.md "Plan destination — ASK BEFORE CREATING" HARD RULE).
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [prediction, ao-dispatch, satellite-batch, ag-closeout-audit, live-capture]
related:
  [
    /plans/active/issues/prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/issues/ag_closeout_audit_prediction_parked_2026_08_21.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
gate_on_depends: false
source: >-
  ag-closeout-audit prediction tranche, Phase 2/3 sweep, 2026-08-21 (sub-agent dispatch), re-verifying
  `plans/active/issues/ag_closeout_audit_prediction_parked_2026_08_21.md`'s orphan-table row for
  `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md` ("3 items redirect
  to cross_ag_live_capture_parity_2026_08_14.md (not in covering set)"). Re-read both docs in full: confirmed the
  redirect target is itself a LOCAL (`assigned_vm: NA`, `execution_scope: local-only`) coordination doc, not an
  AO-dispatched covering plan — so the "redirect" never actually resolves to dispatched work. Conflict-checked via
  `grep -rl "cache_refresh_consumer\|InstrumentCacheRefreshConsumer"` and
  `grep -ril "polymarket.*catalog.*writer"` across `plans/active/*.md`: only the source issue doc and the
  redirect-target coordination doc mention these mechanisms; no existing satellite batch (1-15, any tranche) or
  active plan claims this work. `status: draft` per this skill's own HARD rule (never auto-ship a drafted batch).
context_scope:
  [
    /plans/active/issues/prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/websocket_streaming_handler.py,
  ]
---

# Prediction satellite AO dispatch batch 16 — 2026-08-21

> **Note on epic assignment**: todo 1 below touches `websocket_streaming_handler.py`/`websocket_runner.py`, the
> shared live-capture entrypoint used by every asset group's live VMs (not a prediction-scoped file). Per CLAUDE.md's
> epic-assignment rule ("shared-mechanism, even found via one asset group -> the owning epic"), this arguably belongs
> under `batch_live_symmetry_master` (cross-cutting) rather than `predictions_master` — the source issue doc itself
> declares `parent_epic: batch_live_symmetry_master`. This batch keeps `predictions_master` (one of the two options
> this skill's task explicitly allows: "the source doc's own parent_epic OR the closeout plan's") to match the
> `prediction_satellite_ao_dispatch_batchN` naming convention and avoid touching the cross-cutting tranche's own
> concurrent audit — but an operator/epic-owner may want to re-home todo 1 under `batch_live_symmetry_master` at
> promotion time. Flagged here rather than silently decided.

## Todos

- [ ] [CODE] P1. **Wire `cache_refresh_consumer=` into `LiveWebsocketRunner(...)` in
      `websocket_streaming_handler.py::run()`** (or add an equivalent periodic full-day re-resolution loop), so a
      running prediction shard re-reads `instrument_availability/by_date/day={today}` as the wall-clock date rolls
      and picks up newly-listed markets instead of resolving its instrument universe exactly once at boot and never
      again. The hot-reload path (`InstrumentCacheRefreshConsumer` / `apply_instrument_delta`) already EXISTS in
      `market_tick_data_service/live/websocket_runner.py:325-390` — it is simply never constructed with a non-None
      `cache_refresh_consumer` by the real CLI entrypoint
      (`market_tick_data_service/cli/handlers/websocket_streaming_handler.py:220-266`). Repo: market-tick-data-service.
      Source: `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md`, "Root
      cause A" todo (verbatim: "Wire `cache_refresh_consumer=` into the `LiveWebsocketRunner(...)` construction...").
      **Done when**: a live shard running across a UTC day boundary shows a fresh `resolved N instruments` (or
      delta-apply) log line for the new day without a restart, captured rows resume for markets that opened after
      boot, `quality-gates.sh` green on market-tick-data-service, and the source doc's own todo flipped citing the
      SHA.

- [ ] [DATA] P1. **Root-cause why instruments-service's POLYMARKET `instrument_availability` catalog writer stopped
      producing daily catalogs** (KALSHI, same service, same day-range, kept working throughout) — the
      2026-08-15 re-verification narrowed the break point to between 08-08 and 08-10 (not immediately after 08-05 as
      the source doc's title states), ruled out a Gamma-API outage/schema-drift (a live unauthenticated
      `GET gamma-api.polymarket.com/markets` call returns normal HTTP 200 payloads), and found no Cloud Scheduler job
      or GH Actions workflow driving the catalogue build visible from this repo's config — so the trigger mechanism
      (Cloud Run job / VM cron / agent-orchestrator dispatch) needs identifying + its run logs read to confirm
      whether the POLYMARKET leg of the job has simply stopped being invoked. Repo: instruments-service. Source:
      `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md`, "Root cause B"
      todo (verbatim: "Root-cause why instruments-service's Polymarket `instrument_availability` catalog writer
      stopped producing after 2026-08-05 while the KALSHI writer... kept working"). **Done when**: a named cause
      (scheduler paused for this venue, an upstream API change, a silent per-venue exception) with evidence, and
      either a fix (fresh POLYMARKET blobs appear for the current day) or, if genuinely operator/credential-gated
      (e.g. a paused Cloud Scheduler job needing IAM the worker doesn't have), a retag with the blocking detail cited
      — and the source doc's own todo flipped citing both.

- [ ] [CODE] P2. **Diagnose why zero of 319,820 Polymarket rows were ever `captured` even during the 08-03..08-05
      window when the catalog WAS fresh** — is this the same silent-fallthrough class as a connector bug already
      fixed elsewhere on the cross-AG live-capture-parity effort (Finding A / Finding C's BYBIT-FUTURES diagnosis in
      `cross_ag_live_capture_parity_2026_08_14.md` are the closest precedent shapes — a filter/subscribe-framing bug
      that silently no-ops rather than erroring), or a distinct Polymarket-connector-specific bug? Repo:
      market-tick-data-service (`market_tick_data_service/live/connectors/**`). Source:
      `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md`, "Root cause B"
      second todo (verbatim: "Diagnose why zero of 319,820 Polymarket rows were ever `captured` even during the
      08-03..08-05 window when the catalog was fresh"). **Done when**: a named root cause with evidence (log grep +
      code-path trace, mirroring the BYBIT-FUTURES diagnosis method cited above), then either a fix + at least one
      real `captured` Polymarket row post-fix, or a filed follow-up if the fix itself is large enough to need its own
      scoping — and the source doc's own todo flipped citing the finding.

## Conflict-check (per-item)

- **Todo 1** (`cache_refresh_consumer` wiring): `grep -rl "cache_refresh_consumer\|InstrumentCacheRefreshConsumer" plans/active/*.md`
  returns only `cross_ag_live_capture_parity_2026_08_14.md` (the redirect-source coordination doc, which does not
  implement the fix — its own todo at line 224 explicitly stays open "pending this doc's fix") and the source issue
  doc itself. No existing satellite batch (checked 1-15 across every tranche via filename) references this
  mechanism. Clear.
- **Todo 2** (Polymarket catalog writer root-cause): `grep -ril "polymarket.*catalog.*writer\|catalog.*stopped.*producing" plans/active/*.md`
  returns the source issue doc, `cross_ag_live_capture_parity_2026_08_14.md` (redirect only, no fix), and
  `empty_confirmed_and_coverage_correctness_audit_2026_08_15.md` — that doc's own todo (line ~255) only VERIFIED the
  gap is a real, unabsorbed production outage (not silently masked as honest `SOURCE_RETURNED_ZERO`) and explicitly
  redirects the actual root-cause/fix work to this same source issue doc — it does not claim the root-cause todo
  itself. Clear.
- **Todo 3** (zero-ever-captured Polymarket diagnosis): same grep sweep as todo 2 plus a direct search for "319,820"
  / "zero.*captured.*polymarket" — no hits outside the source doc. Clear.

## Progress Log

- **2026-08-21 (ag-closeout-audit prediction tranche, Phase 3 sub-agent sweep)**: drafted after re-reading
  `prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md` end-to-end (not just
  the parked doc's one-line summary) and confirming its "redirect to cross_ag_live_capture_parity_2026_08_14.md"
  disposition — repeated across 6 na-eligibility-audit passes 2026-08-14→2026-08-21 — never actually resolves to
  dispatched work, because the redirect target is itself a local/NA coordination doc. Extracted all 3 of the source
  doc's open todos verbatim (with DoD text tightened to this batch's own evidence-citation convention, content
  unchanged). See the parked doc's own updated orphan-table row for the disposition record.
