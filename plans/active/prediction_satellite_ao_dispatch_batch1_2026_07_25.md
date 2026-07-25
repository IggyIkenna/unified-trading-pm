---
doc_type: plan
title: Prediction satellite AO batch 1 — conflict-cleared extraction from the 2026-07-25 orphan audit
summary: >-
  First AO-dispatch batch for prediction (prediction has never had one before, unlike sports). Extracted from the
  2026-07-25 orphan-audit's 13 genuinely-orphaned prediction satellite docs (of 20 audited; 6 more were correctly
  deferred to the SPORTS-side audit as sports+prediction dual-tagged docs, verified no double-counting). A 13-agent
  AO-eligibility-triage workflow found candidate AO-eligible todos across all 13, but the majority carried a flagged
  CONFLICT against `prediction_consolidated_closeout_2026_07_18.md`'s own open todos. Per the operator's explicit
  2026-07-25 instruction to never silently resolve a conflict, this batch contains ONLY the 7 todos from
  `prediction_phase_ab_residuals_2026_07_24.md` — the one doc where the triage found 9 AO-eligible items with only 4
  conflicts, none of which textually overlap 8 of the 9 items (item 9, an instrument_type-canonicalization re-verify,
  was excluded as genuinely conflict-adjacent — see Deferred). Two internally-related items (4 and 5, both append
  findings to the SAME sibling issue doc) were combined into one todo to avoid a same-priority file collision. All other
  conflict-gated candidates across the remaining 12 docs are preserved and queued for the operator, not dropped.
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos: [e2e-testing, instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-1, satellite-docs, conflict-checked]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /autonomous session 2026-07-25, driven by the /ag-closeout-audit skill Phase 3 (conflict-checked next-batch drafting)
  after the prediction orphan-audit found 13 genuinely orphaned docs (of 20; 6 deferred to the sports audit). Triage
  workflow `wf_b8829ea8-6cd` (13 agents, 0 errors); this doc extracts the single highest-yield, lowest-conflict source
  doc (prediction_phase_ab_residuals_2026_07_24.md, 8 of 9 AO-eligible items usable).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Prediction satellite AO batch 1 — conflict-cleared extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 7 todos below are same-priority; items 4/5 from the source triage were combined into todo 5 below
> specifically to avoid a same-file collision (both write to
> `prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`) — verified no other collisions across the
> remaining items (see the triage journal, `subagents/workflows/wf_b8829ea8-6cd/journal.jsonl`).

## Todos

- [ ] [CODE] P1. Fix the dead Kalshi host reintroduced into the live smoke matrix + add the missing regression check.
      Swap `https://trading-api.kalshi.com/trade-api/v2/markets` in
      `e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py:552` (confirmed still present live,
      2026-07-25) back to the elections-subdomain host, and add the `predictions_master` regression check that
      `kalshi_api_migration_to_elections_subdomain_2026_05_20.md` Phase 4 never built, so this can't silently reappear a
      third time. Repo: e2e-testing. **Done when**: `validate_batch_live_smoke_matrix.py` no longer references
      `trading-api.kalshi.com`; a new regression test/assertion exists that fails if that host string reappears anywhere
      in the smoke matrix; the smoke matrix runs green. Source: `prediction_phase_ab_residuals_2026_07_24.md`.
- [ ] [DIAG] P2. Quantify the prediction-store event-capture gap the cefi KALSHI-PERP purge surfaced — diff the
      PREDICTION store's KALSHI/POLYMARKET instrument set against the live Kalshi `/markets` (events host) and
      Polymarket CLOB universe to determine whether event markets (`KXMVESPORTSMULTIGAMEEXTENDED`, `KXMVECROSSCATEGORY`,
      etc.) are captured correctly. No code fix is in scope for this todo, only the quantified finding. Repo:
      market-tick-data-service (prediction store, read-only). **Done when**: a quantified verdict is appended to
      `prediction_capture_incident_remediation_2026_07_06.md`'s Progress Log — either "prediction captures them, purge
      loses nothing" (close) or a named coverage-gap count (N markets missing). Source:
      `prediction_phase_ab_residuals_2026_07_24.md`.
- [ ] [CODE] P1. Add a write-time guardrail in instruments-service so any `*-PERP` venue record must be
      `instrument_type=PERPETUAL` and pass a perp-ticker sanity check (reject event-contract patterns like
      `KXMVE*`/`KXMVECROSSCATEGORY*`), rejected at the writer rather than silently accepted — closes the class of bug
      that let the KALSHI-PERP adapter contaminate cefi with 25,473 fake PERPETUAL rows. Repo: instruments-service
      (`reference_data/adapters/cefi/kalshi_perp.py`, `reference_data/adapters/cefi/polymarket_perp.py`). **Done when**:
      a synthetic event-contract record injected into a `-PERP` feed is rejected at write time (not written to the
      catalogue), proven by a new unit test; `quality-gates.sh` green. Source:
      `prediction_phase_ab_residuals_2026_07_24.md`.
- [ ] [DIAG] P2. Re-measure prediction attempted/captured trajectory on a sampled window now that the pre-fetch
      lifecycle gate (market-tick-data-service@abe0904d) and the active-window catalogue widening
      (instruments-service@41ca79d7) have both shipped, and append the before/after counts. Repo: read-only measurement.
      **Done when**: before/after attempted-vs-captured counts for a sampled window are appended to
      `plans/active/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`'s Progress Log
      (and to the coverage docs if the model description changes). Source:
      `prediction_phase_ab_residuals_2026_07_24.md`.
- [ ] [DIAG] P2. **Combined investigation for
      `prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md` (2 sub-items merged into one todo
      since both append findings to that same doc):** (a) Grep-then-READ the MTDS Polymarket adapter
      (`market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py`),
      `rebuild_prediction_manifest.py`, and any `*migrat*2026_04_19*` script to identify which writer/script produced
      the 3 non-canonical POLYMARKET raw-tick path shapes (#3/#3b/#4, content-verified duplicate of the canonical shape)
      documented in the legacy-dual-write-trees issue, and whether any is still live. (b) Confirm whether
      title/slug/eventSlug (or equivalent human-readable market text) is recoverable from instruments-service's
      `prod/catalog.parquet` (`InstrumentRecord.question`) for the sampled `condition_id`s in the same issue, before any
      delete suggestion is considered for the deep 10-segment tree (shape #4). Repos: market-tick-data-service
      (read-only search), instruments-service (`prod/catalog.parquet`, read-only). **Done when**: (a) a named
      commit/script is identified for each of the 3 path shapes plus a live-vs-historical verdict, AND (b) a yes/no
      title/slug-recoverability verdict with evidence (the specific row(s) checked) — both recorded in
      `plans/active/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`'s Progress Log in
      the same commit. Source: `prediction_phase_ab_residuals_2026_07_24.md`.
- [ ] [CODE] P2. Route every prediction `instrument_id`/`underlying`/`canonical_question_group` writer
      (instruments-service `reference_data/adapters/prediction/kalshi.py` + `.../prediction/polymarket/`,
      market-tick-data-service `market_interface/adapters/prediction/`) through UAC's shared canonical-id-builder
      machinery and add a QG check that fails a non-canonical prediction `instrument_id`/ `canonical_question_group` on
      write, preventing re-drift of the dupes A0 enumerated (lowercase prediction/prediction_market, underlying-asset
      leakage). Repos: instruments-service, market-tick-data-service, unified-api-contracts (new QG check). **Done
      when**: a new QG/test fails on a synthetic non-canonical prediction `instrument_id` or `canonical_question_group`
      write and passes on the current writers; QG green. Source: `prediction_phase_ab_residuals_2026_07_24.md`.
- [ ] [DIAG] P3. Verify whether the existing `lifecycle-catalogue-regen-prediction-daily` cron has already carried the
      shipped underlying + cross-venue `canonical_instrument_id` fields into the live `prod/catalog.parquet` for
      prediction (it already regenerates the catalogue on schedule for other fixes), to determine whether the staged
      full manual regen (gated on the in-flight shared canonical-identity migration settling) is actually still needed.
      Repo: instruments-service (`prod/catalog.parquet`, read-only). **Done when**: a yes/no verdict with the checked
      column names + a row sample is recorded in `prediction_phase_ab_residuals_2026_07_24.md`'s Progress Log. Source:
      `prediction_phase_ab_residuals_2026_07_24.md`.

## Deferred — conflict-gated or excluded (NOT dispatched; queued for operator review)

**Excluded from `prediction_phase_ab_residuals_2026_07_24.md` itself**: item 9 of that doc's 9 AO-eligible candidates
("run a fresh live read of `availability_index.parquet` to check for non-canonical `instrument_type` rows") was excluded
— 2 of the doc's 4 flagged conflicts (against `prediction_consolidated_closeout_2026_07_18.md`'s own "instrument_type
casing/canonicalisation gap to literal 100%" item and its P3 `/data-pipeline-reconciliation` re-run todo) both plausibly
touch this exact same ground.

**Every other orphaned doc excluded entirely** (12 of 13): the 13-agent triage workflow (`wf_b8829ea8-6cd`) found
AO-eligible candidates in `data_completion_prediction_2026_07_15.md` (0 AO-eligible, 21 human-only, 3 conflicts on the
doc generally), `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md` (1, 2 conflicts),
`issues/prediction_arb_live_execution_bridge_2026_07_20.md` (0 AO-eligible, 2 conflicts),
`issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md` (1, 2 conflicts),
`issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` (2, 3 conflicts),
`issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md` (2, 2 conflicts — but see todo 5
above, which independently reaches the same ground via `prediction_phase_ab_residuals`'s citation, conflict-free from
that angle), `prediction_phase_c_data_status_ui_2026_07_24.md` (0 AO-eligible),
`prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` (0 AO-eligible, 1 conflict),
`prediction_phase_e_football_arb_live_2026_07_24.md` (0 AO-eligible),
`predictions_ml_walk_forward_and_arb_2026_06_20.md` (1, 1 conflict),
`predictions_other_bucket_and_ui_drilldown_2026_06_20.md` (1, 1 conflict),
`issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` (1, 5 conflicts). Per the operator's 2026-07-25
instruction, none of these are silently resolved or dispatched here. Full detail is in the triage journal
(`subagents/workflows/wf_b8829ea8-6cd/journal.jsonl`).

Every other orphaned doc's remaining work is human-only (operator sign-off, unbuilt safety tooling, cross-repo
architecture decision, or a genuine design/judgment call — e.g. `data_completion_prediction_2026_07_15.md`'s 21
human-only items include a live-production candle-pipeline change the doc itself says needs "a dedicated engineering
session with judgment and staged verification, not a bounded solo-worker task").

> **Re-check status (2026-07-25, `/ag-closeout-audit` batchN re-triage)**: all 12 fully-deferred docs + the excluded
> item 9 above were re-checked against the CURRENT content of `prediction_consolidated_closeout_2026_07_18.md` per the
> skill's batchN methodology. 6 of the 13 candidates cleared conflict-free (2 turned out to be duplicates of work
> already in this plan's own todos above, contributing no new work; the other 6 produced new, conflict-free AO-eligible
> todos) and were extracted into `prediction_satellite_ao_dispatch_batch2_2026_07_25.md` (+ its gated
> `..._batch2_finalize_2026_07_25.md`), both `status: draft`. The remainder stay genuinely blocked — see batch2's own
> Deferred section for the per-item current-state note.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25.md`
(`depends_on: [prediction_satellite_ao_dispatch_batch1_2026_07_25]` + `gate_on_depends: true`), mirroring the
sports/tradfi finalize-plan pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc.
