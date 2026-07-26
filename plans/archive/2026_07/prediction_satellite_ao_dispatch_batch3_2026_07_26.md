---
doc_type: plan
title: Prediction satellite AO batch 3 — fresh Phase-1/Phase-3 triage of the prediction closeout-orphan corpus
summary: >-
  Third AO-dispatch batch for prediction (the last of the 5 asset groups to get this treatment this session), produced
  by the `/ag-closeout-audit` skill's full Phase-1 (per-doc classify) + Phase-3 (conflict-check + draft) triage over all
  17 prediction AG-primary docs not already covered by the consolidated closeout, satellite batch1 (+finalize),
  satellite batch2 (+finalize, both still `status: draft`, undispatched), the 4 forked Phase children (ab-residuals,
  c-data-status-ui, d-formal-smoke-and-backfill, e-football-arb-live), native-ao-extract (+finalize), and
  cross-cutting-debt-index (2026-07-26). 14 docs came back orphaned (10 partial coverage, 4 never touched) — the highest
  orphan rate of any AG this session, mostly because prior batches deferred docs as operator/human-gated without closing
  them. Cross-checked against `sports_satellite_ao_dispatch_batch5_2026_07_26.md` (active) since several prediction docs
  are sports-dual-tagged — found 2 candidates (`sports_odds_feature_naming_four_way_mismatch`,
  `sports_odds_feature_naming_canonicalization`) already have an in-flight, unshipped todo there and excluded them to
  avoid duplicate dispatch. Phase 3 cleared only 2 of the remaining orphans into fresh AO-dispatch todos; left 7
  operator-gated, 1 time-gated, and 1 human-only item (plus the 2 already-covered-elsewhere notes) in the Deferred
  sections below.
status: complete
nature: process
asset_group: [prediction]
stage: [data]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    instruments-service,
    features-service,
    execution-service,
    unified-api-contracts,
  ]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-3, satellite-docs, fresh-triage]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/prediction_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (interactive, operator-approved scope) — Phase 1 classified all 17 prediction
  AG-primary docs not already in the covering-plan set via a Workflow fan-out (17 agents), Phase 3 ran a conflict-check
  + candidate-todo draft over the 14 orphaned docs via a second Workflow fan-out (14 agents, 1 retried individually
  after a StructuredOutput retry-cap failure), per the skill's documented methodology.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Prediction satellite AO batch 3 — fresh triage extraction

> **🟢 ARCHIVED 2026-07-26.** Both todos' dispatch-cycle work is done: todo 1's schema-drift half shipped
> (`unified-api-contracts@c03161a1`) with its paper-order-flow half migrated to its own tracked issue doc
> (`/plans/active/issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`, `BLK-c2d1fff9`, human-only
> credential decision); todo 2's `[OPERATOR]` residual close-out migrated to its own source doc
> (`/plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`, now `assigned_vm: planning`) so
> it stays dispatchable. Archived via `/plans/active/prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`
> (archived alongside this doc, same commit).
>
> **Status: active — operator-approved 2026-07-26.** Dispatched per CLAUDE.md's plan-destination rule and the
> ag-closeout-audit skill's autonomous-mode guidance (a skill-drafted AO batch is never auto-shipped; this flip followed
> explicit operator review). Both todos below touch distinct files/docs — safe to dispatch concurrently.

## Todos

- [ ] [DATA] P1. BLOCKED-OPERATOR (BLK-c2d1fff9) — **PARTIAL 2026-07-26 (slot-7, `data_engineering`): schema-drift half
      DONE, paper-order-flow half blocked on a human-only credential-wiring decision (see below).** **Schema-drift chain
      (DONE)**: the "23 endpoints" turned out to be ONE weekly auto-filed snapshot issue listing all currently-failing
      endpoints (only 2 of 23 are Kalshi), not 23 separate per-endpoint issues — root-caused: NOT a live regression,
      `KalshiMarket` (schemas.py) + the endpoint registry already correctly document the March-2026 dollar-field
      migration; only the 2 VCR cassette fixtures (`markets.yaml`, `market_lookup.yaml`) used as the drift-diff baseline
      were stale (pre-migration shape / an expired test ticker). Re-recorded both against live data;
      `validate_schemas.py` + all 4 `tests/vcr/test_kalshi_vcr.py` tests green. Shipped
      `unified-api-contracts@c03161a1`. Closed the 10 superseded weekly snapshots
      (#45,#46,#47,#60,#102,#319,#416,#541,#555,#590) as duplicates of #673; commented on #673 with the fix (the other
      21 unrelated endpoint failures in that snapshot are untouched, out of scope). **Paper-order flow (BLOCKED)**:
      found the REAL reason it "was never verified" — `execution_service/adapters/sports_factory.py` wires the Kalshi
      adapter to secrets `kalshi-api-key-id`/`kalshi-private-key-pem`, NEITHER of which exists in Secret Manager
      (confirmed `NOT_FOUND`); the actual credential lives under a differently-shaped bundled secret
      (`kalshi-api-credentials`). Any real order attempt fails immediately at secret-load time. This is a genuine
      architecture/ops call (re-provision vs. adapt the code) touching live trading-exchange credentials
      (wallet-key-adjacent, human-only per CLAUDE.md) — filed
      `plans/active/issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` + escalated `BLK-c2d1fff9`,
      did not touch/re-provision the credential myself. Source:
      `plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`. Done when: every open issue in the
      #45→#590 chain has a filed schema-bump PR or a closed-with-evidence resolution (✅ DONE), AND a paper-order-flow
      run's logs/evidence are committed/linked proving the Kalshi execution path works end-to-end (⏳ gated on
      BLK-c2d1fff9's answer).
- [ ] [OPERATOR] P1. **Combined residual close-out for `prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`'s
      remaining 4 uncovered items (batch2's OPERATOR todo covered only 2 of the doc's 4 residual sets; these are the
      other 2, all against the SAME prediction manifest `_index` — merged into one todo to avoid a concurrent-write
      race):** (a) Diagnose and, only if confirmed safe/superseded, purge the 189 blank/UNKNOWN-venue rows against the
      live prediction `_index` (`market-data-tick-pred-prd-central-element-323112`), following the
      `purge_prediction_index_final_residuals_2026_07_11.py` snapshot-then-write, stop-on-surprise-reverify precedent.
      (b) Re-evaluate the ~2,414 remaining non-`captured` schema_version=4/5-family rows left out of the 2026-07-11
      6,760-row purge (remediation step 4's unfinished remainder) — confirm superseded-by-bundle or genuine surviving
      evidence, purge only the former. (c) Re-run `--unphantom-only --apply` against the live prediction corpus (the
      held Phase-B DATA re-emit unblocked by `unified-api-contracts@e7ed754e`'s live-prefix union) to get the first
      defensible genuine-vs-recoverable split for the 13,292 Class-B phantom rows; record the resulting
      genuine-honest-absence count. (d) Re-run `rebuild_prediction_manifest.py` once more (or confirm a rebuild has
      already run since `market-tick-data-service@3397e7ae` landed) so the ~11,988 KALSHI rows mislabeled
      `pipeline_mode=batch_polymarket_clob`/`source=polymarket_clob` self-correct to the venue-resolved values; verify
      via a live count of remaining mislabeled KALSHI rows (expect 0). **Tagged `[OPERATOR]`** per `task_template.md` §3
      delete-risk rule + `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — (a) and (b) purge/mutate live
      prediction-manifest rows and (c)/(d) rewrite live manifest capture_status/provenance values on the same `_index`;
      snapshot-then-write is explicitly not an adequate substitute for the codex's Part-2 content-verify proof, so human
      review/execution is required. **Done when**: for (a) and (b), a fresh live read of each predicate is recorded
      (count + capture_status breakdown) and each row is either purged with a delta logged or explicitly left in place
      with the finding recorded; for (c), the `--unphantom-only --apply` run's before/after recovered-row count is
      recorded as the first defensible genuine-vs-recoverable Class-B split; for (d), a live count confirms 0 (or a
      materially reduced count with rationale) `batch_polymarket_clob`-mislabeled KALSHI rows remain. All four recorded
      in this doc's Progress Log in the same commit, and the doc's `status:` flipped from `open` to `resolved` only if
      all four close cleanly. Source: `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`.

## Deferred — already covered elsewhere (excluded from this batch to avoid duplicating an in-flight AO dispatch)

- **`plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`** and
  **`plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md`**: both describe the same ml-service
  odds-feature-naming migration already extracted as a single combined todo in
  `sports_satellite_ao_dispatch_batch5_2026_07_26.md` (active, unshipped as of this audit) — drafting a second todo here
  would duplicate an in-flight AO dispatch. No action needed in this batch; re-check on the next iteration if batch5's
  todo has landed.
- **`plans/active/issues/sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md`**: mixed
  disposition across its 3-item "Recommended next step" — item 1 (checkbox flip) is already
  sports_satellite_ao_dispatch_batch5's job; item 2 (uncommitted diff) is stale, the underlying code shipped verified
  (`features-service@0ded2449`); item 3 (re-flag the parent plan's dispatch-track designation) remains genuinely open
  but is operator_gated (see below).

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`plans/active/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`**: Confirmed via
  full doc read: the doc is `status: open` (ROUND 7, 2026-07-24) with the operator-gate stated explicitly in its own
  text — "BLOCKED-OPERATOR-DECISION on scheduling that work... Do NOT re-attempt manifest remediation until it ships"
  and "this needs operator sign-off before any code/job change, not an autonomous patch." Uncovered items:... **RE-CHECK
  2026-07-26** (finalize todo 2): still open, but partially de-risked — the code fix todo 12 prescribes
  (manifest-consolidator TOCTOU CAS fix in `_write_consolidated()`) has since shipped
  (`unified-trading-library@14301571`, 2026-07-24) and was proven stable in production on a sibling bucket. Todo 13
  (deploy confirmation to the `instruments-sports` consolidator specifically) and todo 14 (re-run + multi-cycle
  hold-verify against THIS bucket) remain undone, and no operator sign-off authorizing a third remediation attempt on
  this twice-reverted live index has been recorded. Still genuinely gated — leave deferred.
- **`plans/active/issues/prediction_arb_live_execution_bridge_2026_07_20.md`**: Conflict check (step 2): grepped every
  covering-set doc for the two uncovered items' target files/mechanisms (`EventTransport`,
  `AtomicLegExecutor`/`atomic_leg_executor`, `betfair.*lay`, `back+lay`, `CanonicalOdds`) — zero hits anywhere in the
  covering set. The only references to this doc at all are acknowledgment-only:...
- **`plans/active/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`**: The single
  remaining uncovered item is the `[ ] [INFRA] P1 [BLOCKED-OPERATOR-DECISION]` todo (source doc lines 117-121): "Launch
  the historical prediction re-backfill under the widened catalogue." Confirmed by direct read: this is not merely
  tagged BLOCKED-OPERATOR-DECISION as a label of convenience — the doc's own Progress Log states explicitly...
- **`plans/active/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`**: Confirmed Phase-1
  finding: the doc's uncovered remainder is the 3-step sequence in todos 4-6 (design the extended canonical `trades`
  schema → update the MTDS Polymarket writer + migrate the 2,477 `prediction_trades` rows + shape-#4's 158+ objects →
  register in the cutover/non-canonical inventories), all still `- [ ]` open despite the Q3 operator... **GATE CLEARED
  2026-07-26** (`prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md` todo 2's re-check): the Q3 ruling
  landed 2026-07-25 (`unified-trading-pm@7dfcfe0ee`) — extend the canonical `trades` schema, migrate without loss — one
  day BEFORE this batch3 doc's own 2026-07-26 audit, so this was a same-day staleness gap, not a decision made during
  the re-check. The now-unblocked migration work is extracted as a new dispatched todo in
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` (still `status: draft`) instead of staying deferred here.
- **`plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md`**: Confirmed via full read: the doc has
  exactly 2 remaining uncovered open items (item 3, the sentinel fan-out, is fully implemented+cited by
  prediction_satellite_ao_dispatch_batch2_2026_07_25.md, Source-cited back to this doc — not re-extracted here).
  CONFLICT CHECK: grepped the entire covering set (closeout, batch1/batch1-finalize,...
- **`plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`**: Conflict check: grepped the full
  covering set for arb_decay|decay_window|alpha_gate|SportsArbDutchingEngine|SPORTS_ARB_ALPHA_GATE. Three hits, none
  overlapping: (1) prediction_consolidated_closeout_2026_07_18.md lines 491-493 is a pure inventory digest link (no todo
  claiming/closing the work, explicitly says "primary tracking: sports_master"); (2)...
- **`plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md`**: Confirmed via direct read: the two
  uncovered items are todo 3 and todo 5 in `sports_group_c_execution_backtest_harness_2026_07_21.md`, both explicitly
  tagged [DESIGN] by the source doc's own author. Todo 3: resolve whether `SportsMatchingEngine`
  (execution_service/matching_engine/sports_matching.py, zero callers) is dead code to delete, or was...
- **`plans/active/issues/sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md`** (item 3 only):
  re-flag whether `sports_odds_feature_naming_canonicalization_2026_07_21.md` should stay `assigned_vm: NA`/local-only
  given real migration code keeps landing against it piecemeal — a dispatch-track designation call, not a
  worker-executable bounded outcome.

## Deferred — time-gated (re-check on the next batch iteration)

- **`plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md`**: Confirmed via direct read: the doc's 4 uncovered
  P0/P1 items (walk-forward run, acceptance-metrics run, Group-F AUC/calibration gate decision, ml-models registry
  persistence) form one dependency chain rooted entirely on sports_master:Group E -- "Block predictions Group E until
  FSS produces >=95% non-NULL features for trained universe at the...

## Deferred — human-only (needs a dedicated engineering/design session, not an AO todo)

- **`plans/active/data_completion_prediction_2026_07_15.md`**: No new candidate_todo drafted. The doc's remaining work
  was already exhaustively re-triaged twice by the most recent prior batches
  (prediction_satellite_ao_dispatch_batch1_2026_07_25.md and batch2_2026_07_25.md, both dated 2026-07-25), each
  independently concluding "0 AO-eligible (21 human-only items unchanged), 3 conflicts logged against the doc...

## Progress Log

- 2026-07-26 (slot 2): Re-dispatched `prediction_satellite_ao_dispatch_batch3-003` (the Kalshi schema-drift +
  paper-order-flow todo) — found no new work to do; `BLK-c2d1fff9` (the paper-order-flow half's human-only
  credential-wiring decision, per `issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`) is still
  unanswered. Root-caused WHY it got redispatched despite slot-7's `BLOCKED-OPERATOR` annotation: the token was on the
  todo's SECOND physical line, invisible to `regen_backlog_from_plan.py`'s `_parse_open_todos` (which only scans line 1
  — the exact word-wrap gotcha `task_template.md` warns about). Moved `BLOCKED-OPERATOR (BLK-c2d1fff9)` onto the todo's
  first physical line so this stops re-dispatching while the credential decision is still open. No attempt made to rule
  on the credential decision itself — it is wallet-key-adjacent (live trading-exchange credentials), a CLAUDE.md
  human-only hard-stop, not something for a worker or `main` to resolve.
