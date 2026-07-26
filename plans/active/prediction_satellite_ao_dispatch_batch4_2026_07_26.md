---
doc_type: plan
title: Prediction satellite AO batch 4 — the un-triaged A3-relocated sibling-doc gap (cross-venue-arb + live-clob-depth)
summary: >-
  Fourth AO-dispatch batch for prediction, produced by the `/ag-closeout-audit prediction` scheduled run 2026-07-26
  (ag_closeout_auditor, slot 7). Phase 1 re-classified all 26 prediction AG-primary candidate docs via a Workflow
  fan-out (26 agents, 0 errors); Phase 3 reconciled the result against the same-day `batch3` (itself an
  ag-closeout-audit output). The one genuine NEW gap batch3 missed: the three sibling docs that
  `prediction_phase_ab_residuals_2026_07_24.md`'s A3 item relocated its residuals into —
  `prediction_cross_venue_arb_and_coverage_2026_07_24.md`, `prediction_live_clob_depth_capture_2026_07_24.md`, and
  `prediction_perps_kalshi_polymarket_parked_2026_07_24.md` — are cited ONLY in the consolidated-closeout digest and
  were never triaged by any batch (batch1/2/3/native_ao). This batch extracts the conflict-clear, bounded,
  prediction-scoped AO-eligible items out of those docs. Every OTHER prediction orphan (other_bucket, phase_ab/c/d/e,
  data_completion, arb_bridge, lifecycle_prefetch, polymarket_dual_write, cross_ag_bleed, the sports-shared docs,
  ml_walk_forward) was already triaged + deferred by `prediction_satellite_ao_dispatch_batch3_2026_07_26.md`
  (operator/time/human-gated) — NOT re-drafted here, cited in the Deferred section. `status: draft` — a skill-drafted AO
  batch is never auto-shipped; flipping to `active` to dispatch is an operator decision (CLAUDE.md "Plan destination —
  ASK BEFORE CREATING").
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    market-data-processing-service,
  ]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-4, satellite-docs, sibling-gap]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_perps_kalshi_polymarket_parked_2026_07_24.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit prediction scheduled run 2026-07-26 (ag_closeout_auditor, slot 7, dispatch agt-205487) — Phase 1
  classified all 26 prediction AG-primary docs not in the covering-plan set via a Workflow fan-out (26 agents, 0 errors,
  2.16M subagent tokens); Phase 3 reconciled against the same-day batch3 and found the 3 A3-relocated sibling docs
  (cross_venue_arb / live_clob_depth / perps) were never triaged by any batch. Conflict-check + dispatch-scope test per
  the skill's documented methodology.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Prediction satellite AO batch 4 — un-triaged sibling-doc gap extraction

> **Status: draft — NOT dispatched.** This batch was drafted autonomously by the `/ag-closeout-audit prediction`
> scheduled run (2026-07-26). Per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE and the
> ag-closeout-audit skill's autonomous-mode guidance, a skill-drafted AO batch is never auto-shipped: flipping
> `status: draft` → `active` to actually dispatch these todos is an operator decision. The three dispatched todos below
> touch distinct files (IS-adapter-lifecycle / MDPS-retention-read-only / IS-cqg-catalogue) — safe to dispatch
> concurrently once activated.

## Why this batch exists (the gap batch3 missed)

`prediction_satellite_ao_dispatch_batch3_2026_07_26.md` is itself a same-day ag-closeout-audit output that triaged 17
prediction docs. Its candidate set excluded the 4 forked Phase children AND never reached the 3 sibling docs that
`prediction_phase_ab_residuals_2026_07_24.md`'s A3 "close 12 residuals" item explicitly relocated its work into
(`prediction_perps_kalshi_polymarket_parked`, `prediction_live_clob_depth_capture`,
`prediction_cross_venue_arb_and_coverage`). Grep confirms: those 3 basenames appear in ZERO batch/native_ao plan and are
never mentioned by batch3 — they are cited only in `prediction_consolidated_closeout_2026_07_18.md`'s "Aggregated source
docs" digest (the confirmed DIGEST TRAP: listing ≠ dispatch). This batch closes that specific gap.

## Todos

- [ ] [SCRIPT] P0. **Populate POLYMARKET + KALSHI instrument lifecycle
      (`available_from_datetime`/`available_to_datetime`) on the write path + bound honest-absence emission to the
      lifecycle window.** (1) instruments-service: the POLYMARKET gamma raw-market enumeration MUST set
      `available_from_datetime` from gamma `startDate`/`createdAt` + `available_to_datetime` from `endDate`/`closedTime`
      (today both NULL → 0/25); apply the SAME check for KALSHI (the adapter sets `market_created_at`/`resolution_time`
      on `MarketLifecycle` — verify those flow onto the `InstrumentRecord`'s `available_from/to_datetime`). (2)
      market-tick-data-service / UTL honest-absence emission: only emit a cell (captured/empty/failed) for dates WITHIN
      `[available_from, available_to]`; outside the market's life = honest BLANK / `expected_unattempted`, NEVER
      `empty_confirmed`. (3) unified-api-contracts: per the operator's stated direction ("better to have the blanks
      where we expected data", empty_confirmed drill-down 2026-06-23), evaluate whether
      `EXPECTED_INSTRUMENT_NOT_LISTED`/`PRE_VENUE_LAUNCH`/`DELISTED` should be REMOVED from `EMPTY_CONFIRMED_REASONS` so
      out-of-lifecycle dates read as absence, not empty_confirmed. This is the bounded CODE leg only — the historical
      manifest re-walk to reclassify already-written rows is the SEPARATE `[OPERATOR]` walk in the Deferred section
      (gated on this todo landing). Repo: instruments-service + market-tick-data-service + unified-api-contracts.
      Source: `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (P0 lifecycle/empty-emission item, "BIG finding —
      data-correctness, honest-coverage semantics"). **Done when**: the POLYMARKET + KALSHI write paths populate
      `available_from/to_datetime` (proven by a new/extended unit test asserting non-NULL bounds from a fixture
      gamma/kalshi market), the emission path bounds captured/empty/failed cells to the lifecycle window (unit test: an
      out-of-lifecycle date yields absence/`expected_unattempted`, not `empty_confirmed`), the UAC
      `EMPTY_CONFIRMED_REASONS` decision is landed with rationale, and `quality-gates.sh` is green across all three
      repos.

- [ ] [DATA] P2. **Verify END-TO-END MDPS prediction depth-history retention.** The raw live prediction book store is a
      rolling-latest-window (does not retain multi-hour history by itself). Confirm (a) MDPS's prediction live-scan
      cadence against the raw live-book flush window, and (b) that the PROCESSED prediction book/candle store actually
      accumulates multi-hour history rather than only mirroring the rolling raw window — a bounded read/grep of the MDPS
      scan config + a GCS-timespan check on the processed prediction store, with a stated pass/fail verdict. Repo:
      market-data-processing-service (+ market-tick-data-service read-only for the raw-window comparison). Source:
      `prediction_live_clob_depth_capture_2026_07_24.md` (P2 "Verify END-TO-END depth-history retention"). **Done
      when**: a dated verdict is recorded (PASS = processed store demonstrably accumulates >1 flush-window of prediction
      depth history, with the measured processed-store time span cited; or FAIL = a named retention gap + the specific
      scan-cadence/flush-window mismatch), committed to that doc's Progress Log. Read-only verification — no data
      mutation.

- [ ] [SCRIPT] P2. **cqg recent-window catalogue re-enumeration with the already-fixed classifier.** The cqg-partitioned
      `instrument_availability` catalogue (instruments-store) is refreshed for 2026-06-23 only (34 groups verified);
      re-enumerate the recent enumerated window (2026-06-20..22) with the fixed cqg classifier so those dates' catalogue
      also carries real `canonical_question_group` values. This is an operational run of the ALREADY-FIXED classifier
      over a bounded 3-day window (deep history is the bulk-tick-seed with no per-date catalogue — out of scope here).
      This touches the IS cqg-catalogue enumeration module, DISTINCT from todo #1's adapter-lifecycle write path (no
      file collision). Repo: instruments-service. Source: `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (P2
      "cqg partition-completeness — recent-window catalogue re-enumeration"). **Done when**: the 2026-06-20..22 cqg
      catalogue partitions are re-enumerated and a live read confirms each of those 3 dates now carries populated
      `canonical_question_group` catalogue rows (count cited), with the run's evidence recorded in the source doc's
      Progress Log.

- [ ] [CODE] P1. **Extend the canonical `trades` schema for POLYMARKET metadata + migrate the legacy `prediction_trades`
      population, now that the doc's Q3 operator-decision gate has cleared.** Operator ruling 2026-07-25
      (`unified-trading-pm@7dfcfe0ee`,
      `plans/active/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`): extend the
      canonical `data_type=trades` schema (currently 5 columns) rather than drop the legacy metadata or permanently fork
      a separate canonical shape. (1) unified-api-contracts: add `title`/`slug`/`event_slug`/`outcome`/ `outcome_index`
      as first-class canonical `trades` fields — the operator-directed minimum set (market-question + resolution
      metadata with no surviving copy elsewhere). Do NOT add the trader-identity fields (`proxy_wallet`/
      `name`/`pseudonym`/`bio`/`profile_image`) — those are explicitly flagged PII-adjacent in the operator ruling and
      need a SEPARATE operator call on whether they're genuinely needed downstream; leave them out of this pass. (2)
      market-tick-data-service: update the Polymarket CLOB writer to emit the extended schema going forward. (3) Migrate
      the 2,477 `data_type=prediction_trades` manifest rows + shape-#4's 158+ objects into the canonical
      `data_type=trades` path/shape under the extended schema — copy+verify+delete per the standard delete-safety
      protocol (content-verify before any delete, no data loss). (4) Register the extended schema + migration in
      `canonical-cutover-register.md` + `non-canonical-path-inventory.md`. Repo: unified-api-contracts,
      market-tick-data-service, unified-trading-pm. Source:
      `prediction_polymarket_legacy_dual_write_trees_metadata_     loss_2026_07_24.md` todos 4-6 — batch3 deferred this
      doc as operator-gated on Q3; the `prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md` re-check
      (2026-07-26) confirmed Q3 cleared the SAME day batch3 was drafted (the ruling landed 2026-07-25, one day before
      batch3's 2026-07-26 audit — a same-day staleness gap, not a new decision made during this re-check). **Done
      when**: UAC's `trades` schema carries the 5 new fields (PII fields explicitly excluded, with the exclusion
      recorded as a still-open separate decision); the writer emits them; the 2,477+158 legacy rows are migrated with a
      verified 0-loss content-check; the cutover/non-canonical inventories are updated; `quality-gates.sh` is green
      across all three repos.

## Deferred — gated on a sibling todo landing (NOT dispatched speculatively)

- **[OPERATOR][DATA] Combined prediction `_index` manifest canonicalisation single-walk** (rides ONE prediction
  single-walk — single-walk discipline, NOT a standalone whole-corpus walk): (a) reclassify the ~49.6k out-of-lifecycle
  POLYMARKET `empty_confirmed` rows to honest absence per todo #1's newly-populated lifecycle bounds (also audit whether
  the 93,264 `SOURCE_RETURNED_ZERO` include out-of-lifecycle dates); (b) map the ~124 lowercase `venue=kalshi` →
  `KALSHI` + resolve the ~168 blank / ~21 `UNKNOWN`-venue rows (phantom denominator split); (c) re-walk the 1,454
  prediction `_index` rows still at schema v4 up to v9. **Gated on todo #1 landing** (the out-of-lifecycle
  reclassification needs the lifecycle bounds to exist first) and **`[OPERATOR]`** — a manual manifest `--apply` flips
  real captured→attempted_failed on a false positive (CLAUDE.md +
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`), so human review/execution is required; bundled into ONE
  walk to avoid concurrent-write races on the same `_index`. Source:
  `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (P2/P3 residual-manifest items, both "NICE-TO-HAVE", both
  "ride the next prediction canonicalisation walk").
- **[OPERATOR][SCRIPT] Re-enumerate the IS POLYMARKET universe for a recent past date → re-run the `book_snapshot_5`
  batch backfill → verify `row_count>0`.** A bounded, idempotent re-enumeration+backfill, but it (a) shares the
  POLYMARKET IS enumeration path with todo #1 so it should sequence AFTER #1 lands (else it re-enumerates against the
  old write path), and (b) launches a backfill VM → `[OPERATOR]` per the VM-launch gating rule (safe-idempotent
  justification: the shard re-runs cleanly on preemption). Source: `prediction_live_clob_depth_capture_2026_07_24.md`
  (the "DEFERRED-CROSS-DEP" `book_snapshot_5` row-proof item).

## Deferred — operator / design-gated (BLOCKED-OPERATOR-DECISION, not a bounded worker outcome)

- **`prediction_cross_venue_arb_and_coverage_2026_07_24.md` [DESIGN] items** — the fixture-pairing residual
  (registry-resolution + mapping-population + arb-layer WIRING across UAC/IS/features/strategy) and the per-instrument
  same-game/same-settlement arb PAIRING within a shared cqg group. Both are tagged `[DESIGN]` by the source author: the
  arb-pairing/wiring semantics are an undecided design call, not a bounded checkable outcome — resolve as a design
  session first, then dispatch the resulting scoped step (dispatch-scope eligibility rule).
- **`prediction_cross_venue_arb_and_coverage_2026_07_24.md` [UAC] Politics/geo cross-venue canonicalization audit** —
  per-family arbability analysis (Kalshi Politics 2049-series vs Polymarket TRUMP/GEO groups). This is a judgment audit
  (which families are genuinely arbable + how to canonicalize them), operator/design-gated, not a mechanical extraction.

## Deferred — cross-cutting (belongs to a different tranche, not prediction)

- **`prediction_cross_venue_arb_and_coverage_2026_07_24.md` [OPS] tarball-overwrite race** (a concurrent fleet
  `create-code-tarballs` from a clone behind LDR clobbers a tarball; fix = SHA-pinned tarball fetch or a build-lock in
  the deployment-service launchers). This is generic deployment/CI infrastructure, not prediction-specific data work —
  it belongs to the `infra`/`ci` tranche's closeout, not a prediction batch. Flagged here so it isn't lost; route it
  there.

## Deferred — time-gated / too-large / upstream-blocked (non-batchable)

- **`prediction_cross_venue_arb_and_coverage_2026_07_24.md` [SCRIPT] series-scoped `/historical/*` Kalshi enumeration**
  to close the 2025-10→2026-04 Kalshi mid-gap — a historical backfill (`[OPERATOR]` VM, heavier); a candidate for a
  future batch or a dedicated backfill plan once todo #1's lifecycle work lands (so the backfill emits honest
  lifecycle-bounded cells), not a same-batch concurrent todo.
- **`prediction_perps_kalshi_polymarket_parked_2026_07_24.md`** — its one open item (the Polymarket-perp enumerator) is
  **BLOCKED-UPSTREAM**: the doc confirms no public Polymarket perps API exists yet. Non-batchable until the upstream
  venue ships one — track, do not re-surface every batch cycle.

## Deferred — already triaged + deferred by batch3 (2026-07-26), NOT re-drafted here

Per the ag-closeout-audit iterative-drain rule (do not re-litigate a prior batch's Deferred section without new
evidence), every other orphaned prediction doc from this run's Phase 1 was already classified by
`prediction_satellite_ao_dispatch_batch3_2026_07_26.md` (a same-day audit output) into its operator/time/human-gated
Deferred buckets. **Update 2026-07-26 (`prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md` todo 2's
re-check)**: one of these gates has since cleared —
`issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss`'s Q3 operator decision was ruled 2026-07-25 (one
day before this batch's own audit, a same-day staleness gap); its now-unblocked migration work is extracted as a
dispatched todo above instead of staying in this Deferred list. Every other gate re-checked the same day: none has
demonstrably cleared. Not re-drafted here (would duplicate batch3's disposition):
`predictions_other_bucket_and_ui_drilldown` (operator/infra-slot-availability-gated),
`issues/prediction_arb_live_execution_bridge` (operator architectural transport-seam decision),
`issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue` (operator — historical re-backfill launch),
`issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index` (operator sign-off — underlying library fix has
shipped and proven stable on a sibling bucket, but sign-off for a third remediation attempt on this specific
twice-reverted index is still outstanding), `sports_arb_decay_window_and_alpha_gate_design` /
`sports_group_c_execution_backtest_harness` / `sports_predictions_live_mode_activation_readiness` /
`sports_odds_feature_naming_canonicalization` (sports-master-owned / design-gated / time-gated),
`predictions_ml_walk_forward_and_arb` (time-gated on sports_master Group E), `data_completion_prediction_2026_07_15`
(human-only — 3× independently re-triaged to 0 AO-eligible). The 4 forked Phase children
(`prediction_phase_ab_residuals` Phase-B fixture-attribute backfill, `prediction_phase_c_data_status_ui`,
`prediction_phase_d_formal_smoke_and_backfill`, `prediction_phase_e_football_arb_live`) are `assigned_vm: NA`
human-track plans whose residuals are dominated by the un-started Phase-B canonicalisation migration (time-gated) —
Phase B itself is a large multi-repo migration that warrants its own dedicated plan, not a batch todo.

## Progress Log

- 2026-07-26 (slot 7, ag_closeout_auditor, dispatch agt-205487): drafted by the `/ag-closeout-audit prediction`
  scheduled run. Phase 1 = 26-agent Workflow (`wf_d800a7e0-975`), 0 errors; verdicts: 10 orphaned_never_touched, 10
  orphaned_partial_coverage, 5 archivable_after_planned_work, 1 exclude_cross_cutting. Phase 3 reconciliation found the
  3 A3-relocated sibling docs (cross_venue_arb / live_clob_depth / perps) were never triaged by any batch
  (grep-confirmed: 0 hits in batch1/2/3/native_ao; 0 mentions in batch3). Extracted 3 conflict-clear bounded todos + 2
  gated-on-#1 `[OPERATOR]` walk/backfill items + the design/cross-cutting/upstream deferrals. Left `status: draft` per
  the autonomous-mode safety rail — operator flips to `active` to dispatch. No new issue doc filed: the orphans are
  already tracked as their own docs; this batch + batch3 are the actionable artifacts.
