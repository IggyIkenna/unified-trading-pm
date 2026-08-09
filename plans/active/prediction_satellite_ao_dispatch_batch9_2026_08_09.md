---
doc_type: plan
title:
  Prediction satellite AO batch 9 — bounded-item extraction from the RECLASSIFY sweep's 2 whole-doc-ineligible
  prediction docs (2026-08-09)
summary: >-
  Satellite-batch extraction mirroring /ag-closeout-audit's pattern, produced from a targeted read of the 2 prediction
  plan docs a same-day RECLASSIFY sweep found did NOT qualify for a whole-doc `assigned_vm` flip.
  prediction_consolidated_closeout_2026_07_18.md is a 0-native-todo coordination hub (archive_exempt, by design) with
  zero extractable items. prediction_cross_venue_arb_and_coverage_2026_07_24.md yielded 2 conflict-clear items — a
  Kalshi historical-backfill build whose prerequisite gate (batch4's own todo #1, POLYMARKET instrument-lifecycle
  bounds) shipped 2026-08-07, and a now-safe operational `--apply` run whose blocking script bug was already fixed.
  Conflict-checked against prediction_satellite_ao_dispatch_batch4/6/7/8 (all active/complete) — zero collisions.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, e2e-testing, unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, satellite-extraction, batch-9, orphan-extraction]
related:
  [
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/prediction_satellite_ao_dispatch_batch9_2026_08_09_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /codex/04-architecture/prediction-batch-live.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py,
  ]
depends_on: []
source: >-
  Targeted satellite-batch extraction (2026-08-09), scoped to the 18-doc list a same-day RECLASSIFY sweep flagged as NOT
  whole-doc-flip-eligible (14 defi + 2 tradfi + 2 prediction). Both prediction candidates read end to end; extractable
  items conflict-checked against every active/recently-drafted prediction satellite batch (4, 6, 7, 8).
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# Prediction satellite AO batch 9 — 2026-08-09

Only 2 items qualified, both from `prediction_cross_venue_arb_and_coverage_2026_07_24.md`.
`prediction_consolidated_closeout_2026_07_18.md` is a coordination hub (`archive_exempt: true`,
`gate_on_depends: false`, 0 native todos by its own frontmatter and design — it only aggregates 4 forked-out Phase A-E
child plans, none of which are in this run's 18-doc scope) and contributed nothing to extract.

## Todos

- [x] [SCRIPT] P1. **Build the series-scoped `/historical/*` Kalshi enumeration to close the 2025-10→2026-04 Kalshi
      trades mid-gap.** ✅ — `instruments-service@3f2ddca0` + `e2e-testing@5e2f90e`. The deep-corpus seed (Jon-Becker
      free Parquet) already covers 2021-06-30→~2025-09, and the recent-window live backfill covers the last ~60 days —
      the 2025-10→2026-04 mid-gap is the precise, bounded residual. Both prerequisites this todo needs are already
      shipped: the IS cutoff-aware date routing (`instruments-service@8b118d9`, live `/markets` vs `/historical/markets`
      by `/historical/cutoff`) and the RSA-PSS auth for the `/historical/*` tier. Built: `KalshiReferenceDataAdapter`
      gained `enumerate_all_series` (unfiltered `GET /series`, ~11k series — the tractable enumeration unit, flat
      market-pagination is infeasible at this scale) / `fetch_series_markets_in_window` (per-series
      `/markets?status=closed`, client-filtered by close_time) / `fetch_historical_trades` (RSA-PSS-signed
      `/historical/trades`, cursor-paginated) / `enumerate_historical_gap_markets` (orchestrator), all shard-isolated +
      429-retried per the existing live series-scoped pattern (7 new unit tests, `instruments-service` QG green). Driver
      `e2e-testing/scripts/prediction/kalshi_historical_gap_backfill.py` wires series→markets→trades→write via the
      standard `record_captured_from_counts`/`record_failed` honest-absence contract, matching the already-established
      canonical schema (`trade_id`/`count`/`yes_price`/`no_price`/`taker_side`/`created_time`/`ticker`/
      `canonical_question_group`/`available_at`) and the exact `pipeline_mode=batch_kalshi`/`source=kalshi` bundle shape
      `ingest_kalshi_bulk_to_canonical.py` already emits (byte-shape-identical, source-blind downstream). The gate this
      todo was originally parked behind — POLYMARKET instrument-lifecycle bounds landing first, so the backfill emits
      honest lifecycle-bounded cells — shipped 2026-08-07 (`instruments-service@3617261f`, confirmed via
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s own finalize-reconciled Progress Log entry). Repos:
      e2e-testing (driver) + instruments-service (series enumerator). Source:
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` ("series-scoped historical backfill" todo, 2026-06-23
      section). **Scope note**: this todo's own "done when" (a manifest read confirming real captured rows across the
      full window) requires an actual ~11k-series production run — VM-scale heavy I/O per
      `/codex/05-infrastructure/vm-launcher-runbook.md`, out of a single dispatched-task session's scope (build the code
      vs. run the campaign are different bounded units). The dispatched task's own `done_definition` was "checkbox
      flipped in plan + code shipped" — satisfied. The production run + manifest verification is tracked as a fresh
      follow-up todo below, not silently folded into this one.
- [ ] [SCRIPT] P1. **Run the now-safe `--apply --venue KALSHI` operational re-walk for cqg batch re-classification.**
      The blocking script bug is already fixed (`market-tick-data-service@24db3f16` — `rebuild_prediction_manifest.py`
      now threads `venue` into `compute_object_atom` and routes `classify_kalshi_to_canonical_group(ticker=cid)` for
      KALSHI vs the tuple path for POLYMARKET, with 2 regression tests + the venue-aware routing verified against real
      tickers, e.g. `KXCPI→CPI_PRINT_PER_MONTH`, `KXMLBGAME→SPORTS_MLB_MATCH`). The run itself remains: (1) a dry-run
      over the dates where Kalshi TICK parquets actually exist (a 2026-05-01..03 sample previously showed `objects:0` —
      find the real seeded-date range first), (2) confirm the dry-run reclassifies to real cqg groups (non-OTHER), (3)
      `--apply` (local or VM, ~5000s at the doc's own prior-measured scale). Re-reads existing tick parquets only — NOT
      a tick migration, no GCS object mutation. Repo: market-tick-data-service. Source:
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` ("cqg partition-completeness — BATCH re-classification
      re-walk" todo, 2026-06-23 section). Done when: the `--apply` run completes with a dry-run-confirmed non-OTHER cqg
      distribution for the reclassified KALSHI dates, and the doc's own note about the 116,192 `SOURCE_RETURNED_ZERO`
      rows lacking `available_from/to` (which stay `empty_confirmed`, unresolvable by this re-walk alone) is preserved
      as a distinct residual, not silently folded into "done".
- [ ] [OPS] P2. **Run the Kalshi historical mid-gap backfill campaign on a VM + manifest-verify closure.** Follow-up to
      the now-shipped series-scoped enumeration (todo 1 above) — that todo built the code; this todo runs it at
      production scale. Launch
      `e2e-testing/scripts/prediction/kalshi_historical_gap_backfill.py --start 2025-10-01     --end 2026-04-21` on a
      dedicated VM per `/codex/05-infrastructure/vm-launcher-runbook.md` (register via `VM_PREFIX_TO_BUCKET`, default
      SPOT, verify STARTED + ongoing progress + a terminal state — no fire-and-forget; ~11k series × throttled
      per-series fetch, expect hours). Before the full run, smoke-test with `--limit-series 5     --dry-run` to confirm
      the live Kalshi API response shapes (`/series`, `/markets?status=closed`, `/historical/trades`) match this todo's
      mocked-response assumptions — the adapter code was built + unit-tested against the documented/inferred Kalshi
      schema without a live credentialed call in the dev sandbox; if a real response shape differs, fix the adapter
      parsing before the full run, don't launch blind. Requires `kalshi-api-credentials` (Secret Manager) for the
      `/historical/*` signed tier — if inaccessible from the VM's identity, status `BLOCKED-CREDENTIALS` and self-grant
      per `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` (do not pause). Done when: a manifest
      read confirms real `captured`/`empty_confirmed` rows for KALSHI trades across the full 2025-10→2026-04 window (the
      todo-1 script's own "done when"), closing the previously-empty mid-gap — cite the manifest read + VM
      run/completion evidence in the checkbox flip.

## Not extracted this batch — items that stay behind

- `prediction_consolidated_closeout_2026_07_18.md` — `archive_exempt: true`, `gate_on_depends: false`, 0 native todos by
  design (a coordination hub referencing 4 forked-out Phase A-E child plans, none of which are in this run's 18-doc
  scope). Nothing to extract.
- `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s `[OPS] P2` tarball-overwrite race item — a design choice
  ("consider SHA-pinned tarball fetch... or a build-lock") not yet resolved to one approach; also already flagged by
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s own Deferred section as belonging to the `infra`/`ci`
  tranche's closeout, not prediction's. Stays behind.
- `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s `[DESIGN] P1` fixture-pairing residual (team-name
  canonicaliser) — already claimed verbatim by the ACTIVE `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s own
  `[DATA] P2` "team-name alias tables" todo — conflict, not re-drafted.

## Progress Log

- 2026-08-09 (targeted satellite-batch extraction, RECLASSIFY-sweep follow-up): drafted alongside its finalize twin. 2
  conflict-clear todos extracted from `prediction_cross_venue_arb_and_coverage_2026_07_24.md`; the sibling
  consolidated-closeout doc contributed zero (0-native-todo hub by design). Both extracted items were previously
  time-gated/blocked in `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s own Deferred section on prerequisites
  that have since shipped (verified via the source doc's own finalize-reconciled Progress Log, not assumed) —
  conflict-check against batch4/6/7/8 found zero collisions on the 2 extracted items themselves.
- 2026-08-09 (todo 1 shipped): `instruments-service@3f2ddca0` adds
  `enumerate_all_series`/`fetch_series_markets_in_window`/`fetch_historical_trades`/`enumerate_historical_gap_markets`
  to `KalshiReferenceDataAdapter` (7 new unit tests, QG green); `e2e-testing@5e2f90e` adds the
  `kalshi_historical_gap_backfill.py` driver wiring series→markets→trades→canonical-write (QG green). Both verified
  ancestors of `origin/live-defi-rollout`. Added a fresh follow-up todo (P2 OPS) for the actual VM-scale production run
  - manifest verification — the code build and the production campaign are different bounded units; this todo's own
    code-ship scope is complete, the campaign is tracked separately, not silently folded in.
