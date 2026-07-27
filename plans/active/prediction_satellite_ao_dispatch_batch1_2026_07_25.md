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
status: active
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
priority: P1
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

- [x] ✅ [CODE] P1. Fix the dead Kalshi host reintroduced into the live smoke matrix + add the missing regression check.
      — `e2e-testing@371ac1b`. `_fetch_kalshi_instruments()` in `validate_batch_live_smoke_matrix.py` now points at
      `api.elections.kalshi.com` (was `trading-api.kalshi.com`, 401s since the 2026-05-20 migration). New
      `tests/unit/test_validate_batch_live_smoke_matrix.py` scans the module's own source for the dead host string (not
      just the one call site) so a third reintroduction anywhere in the file fails the build — wired via a new
      `scripts/validation/` sys.path entry in `tests/unit/conftest.py`. `quality-gates.sh` green.
- [x] ✅ [DIAG] P1. Quantify the prediction-store event-capture gap the cefi KALSHI-PERP purge surfaced — diff the
      PREDICTION store's KALSHI/POLYMARKET instrument set against the live Kalshi `/markets` (events host) and
      Polymarket CLOB universe to determine whether event markets (`KXMVESPORTSMULTIGAMEEXTENDED`, `KXMVECROSSCATEGORY`,
      etc.) are captured correctly. No code fix is in scope for this todo, only the quantified finding. Repo:
      market-tick-data-service (prediction store, read-only). **Done when**: a quantified verdict is appended to
      `prediction_capture_incident_remediation_2026_07_06.md`'s Progress Log — either "prediction captures them, purge
      loses nothing" (close) or a named coverage-gap count (N markets missing). Source:
      `prediction_phase_ab_residuals_2026_07_24.md`. — **NOT a clean close.** Quantified + root-caused in
      `prediction_capture_incident_remediation_2026_07_06.md` Phase 3 (flipped) + new Phase 6 (fix filed, not
      implemented — out of this todo's scope). Verdict: the `KXMVE*` event-contract family this todo named IS correctly
      captured (honest `OTHER`, 21% of Kalshi volume); the real bug is the OTHER 79% of daily Kalshi volume (30 real
      classifiable canonical_question_groups) ALSO landing in `OTHER` due to a one-line write-time bug
      (`instruments-service/instruments_service/engine/orchestrator/prediction.py:95` passes the full `instrument_key`
      instead of the bare ticker into the classifier) — confirmed for every day 2026-07-12 through 2026-07-26.
      Read-only: no code changed.
- [x] ✅ [CODE] P1. **DONE 2026-07-27 (slot-9)** — `instruments-service@a4137022`. Added a shared
      `validate_perp_instrument_record()` write-time guardrail (`reference_data/adapters/cefi/_perp_write_guard.py`),
      wired into both `kalshi_perp.py`'s and `polymarket_perp.py`'s `_parse_market` — rejects any record whose
      `instrument_type` isn't `PERPETUAL`, or whose ticker matches a known event-contract prefix (`KXMVE*`), independent
      of the venue's own category field. This is defense-in-depth on top of Kalshi's existing category check: a
      synthetic market with `category="Crypto"` but a `KXMVECROSSCATEGORY-*` ticker is still rejected (new test
      `test_event_contract_ticker_rejected_even_with_crypto_category`), proving the guardrail catches what the category
      field alone would miss. Polymarket's parser previously had NO rejection filter at all — added the same guard + a
      rejection test (`test_event_contract_ticker_rejected`). New `tests/unit/test_perp_write_guard.py` covers the guard
      function directly (genuine-perp pass, non-PERPETUAL reject, event-contract-ticker reject, case-insensitive).
      `quality-gates.sh` green (263s, then re-verified 149s on the quickmerge pass).
- [x] ✅ [DIAG] P1. Re-measure prediction attempted/captured trajectory on a sampled window now that the pre-fetch
      lifecycle gate (market-tick-data-service@abe0904d) and the active-window catalogue widening
      (instruments-service@41ca79d7) have both shipped, and append the before/after counts. Repo: read-only measurement.
      — `unified-trading-pm`. Before/after counts appended to
      `plans/active/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`'s Progress
      Log: captured fraction of attempted rows 26.3% → 97.9% (+71.6pp), captured rows/day ~46× (44.6 → 2,058.1),
      comparing live-cron-captured windows straddling the 2026-07-14 fix (historical corpus re-backfill is still
      operator-gated, so no historical before/after exists yet — this is the honest currently-measurable comparison). No
      coverage-doc model-description change needed (same honest-absence model, healthier proportions). A separate,
      unrelated anomaly surfaced incidentally (14,095 KALSHI `attempted_failed`/`UNCLASSIFIED_ADAPTER_ERROR` rows
      concentrated on `date=2026-07-26`) and was filed as its own issue doc rather than absorbed into this todo's scope:
      `plans/active/issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md`. Source:
      `prediction_phase_ab_residuals_2026_07_24.md`.
- [x] ✅ [DIAG] P1. **Combined investigation for
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
      the same commit. Source: `prediction_phase_ab_residuals_2026_07_24.md`. — `unified-trading-pm@<pending-sha>`.
      **(a)** all three shapes are HISTORICAL, none written by any live code path today: #3/#3b are the Polymarket
      adapter's pre-2026-04-19 drifted output (fixed forward by `da270f9b`/`ca246a9b`, zero live `"prediction_trades"`
      references at HEAD); #4 was produced solely by the now-DELETED one-off `migrate_polymarket_canonical.py` (added
      `da270f9b` 2026-04-19, deleted `bce12993` 2026-06-10) — superseded by UAC's actual flat canonical grammar
      (`build_prediction_partition_path`, verified 2026-04-29/2026-06-02). The manifest's recent `prediction_trades`
      `written_at` is a re-walk-tool artifact (`rebuild_prediction_manifest.py` re-emitting legacy values verbatim), not
      new capture. **(b)** MIXED: slug fully recoverable (`raw_symbol`, 0% NULL corpus-wide, populated for the sampled
      condition_id), but title/question is NOT reliable (93.2% NULL corpus-wide, NULL for the sampled row despite a
      2026-07-17 questionbackfill attempt), and eventSlug is recoverable NOWHERE (no persisted column). Full evidence in
      the issue doc's Progress Log.
- [ ] [CODE] P1. Route every prediction `instrument_id`/`underlying`/`canonical_question_group` writer
      (instruments-service `reference_data/adapters/prediction/kalshi.py` + `.../prediction/polymarket/`,
      market-tick-data-service `market_interface/adapters/prediction/`) through UAC's shared canonical-id-builder
      machinery and add a QG check that fails a non-canonical prediction `instrument_id`/ `canonical_question_group` on
      write, preventing re-drift of the dupes A0 enumerated (lowercase prediction/prediction_market, underlying-asset
      leakage). Repos: instruments-service, market-tick-data-service, unified-api-contracts (new QG check). **Done
      when**: a new QG/test fails on a synthetic non-canonical prediction `instrument_id` or `canonical_question_group`
      write and passes on the current writers; QG green. Source: `prediction_phase_ab_residuals_2026_07_24.md`.
- [ ] [DIAG] P1. **Conflict-check (2026-07-25 plan-reconcile)**: `prediction_satellite_ao_dispatch_batch2_2026_07_25.md`
      todo 2 ALSO writes to `prediction_phase_ab_residuals_2026_07_24.md`'s Progress Log (and flips a checkbox there).
      Do not dispatch/commit concurrently with that todo — this batch (batch1) was drafted first, run this todo before
      batch2 todo 2 if both are active. Verify whether the existing `lifecycle-catalogue-regen-prediction-daily` cron
      has already carried the shipped underlying + cross-venue `canonical_instrument_id` fields into the live
      `prod/catalog.parquet` for prediction (it already regenerates the catalogue on schedule for other fixes), to
      determine whether the staged full manual regen (gated on the in-flight shared canonical-identity migration
      settling) is actually still needed. Repo: instruments-service (`prod/catalog.parquet`, read-only). **Done when**:
      a yes/no verdict with the checked column names + a row sample is recorded in
      `prediction_phase_ab_residuals_2026_07_24.md`'s Progress Log. Source:
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
