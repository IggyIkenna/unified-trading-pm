---
doc_type: plan
title:
  Prediction satellite AO batch 10 — 4 conflict-clear items unblocked by 2026-08-07/08 rulings, extracted from the daily
  /ag-closeout-audit prediction sweep (2026-08-09)
summary: >-
  Eighth-generation satellite-batch extraction (batch4/6/7/8/9 precede it) produced by the scheduled `/ag-closeout-audit
  prediction` run 2026-08-09 (Phase 1: 37-doc Workflow fan-out, 0 errors — 22 `exclude_cross_cutting`, 4
  `orphaned_partial_coverage`, 4 `orphaned_never_touched`, 6 `archivable_after_planned_work`, 1 `archivable_now`; full
  detail in `issues/ag_closeout_audit_prediction_parked_2026_08_09.md`). Of the 8 genuinely orphaned docs, 4 are
  non-batchable (1 too-large-for-a-batch-todo needing its own dedicated design plan, 1 operator-gated judgment call, 1
  time-gated on an external `sports_master:Group E` cross-tranche dependency, 1 minor infra item punted to the
  `ci`/`infra` tranche) — see this run's parked-findings doc for the full taxonomy breakdown. The 4 items here are the
  conflict-clear remainder: all 4 were previously blocked (2 on an operator judgment call, 2 on a sibling todo's
  prerequisite gate) and all 4 blockers cleared 2026-08-07/08, but none of the 4 items were ever promoted into a live
  dispatched todo anywhere in the tranche's 15-doc covering set — independently re-verified via a fresh basename +
  content-term grep across every active batch/finalize/phase-child doc before drafting.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [prediction, ao-dispatch, satellite-extraction, batch-10, orphan-extraction, dead-code, cqg-backfill]
related:
  [
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/archive/2026_08/issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md,
    /plans/active/issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/prediction_satellite_ao_dispatch_batch10_2026_08_09_finalize.md,
    /plans/active/issues/ag_closeout_audit_prediction_parked_2026_08_09.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/archive/2026_08/issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md,
    /plans/active/issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md,
  ]
depends_on: []
source: >-
  Scheduled `/ag-closeout-audit prediction` run 2026-08-09 (ag_closeout_auditor, slot 14, dispatch agt-465129). Phase 1
  37-agent Workflow fan-out (0 errors) classified every AG-primary candidate; Phase 3 conflict-checked all 8 orphaned
  docs' remaining items against the full 15-doc covering set (consolidated closeout + 4 Phase A-E children + satellite
  batches 4/6/7/8/9 + their finalize plans) and against the dispatch-scope eligibility test
  (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility").
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# Prediction satellite AO batch 10 — 2026-08-09

> **Status: draft — awaiting operator approval to dispatch (CLAUDE.md "Plan destination — ASK BEFORE CREATING" HARD
> RULE).** A skill-drafted AO batch is never auto-shipped; frontmatter `status: draft` (above) is the real ingestion
> gate — a draft is not picked up by `regen_backlog_from_plan.py`. Flipping to `status: active` to actually dispatch
> this batch is an operator decision, parked as a follow-up in this run's `/done` evidence.

4 items, all conflict-clear against the full active covering-doc set (consolidated closeout, 4 Phase A-E children,
satellite batches 4/6/7/8/9 + finalizes — re-verified via basename + content-term grep immediately before drafting, not
assumed from the Phase-1 agents' own grep alone).

## Todos

- [ ] [SCRIPT] P1. **Promote batch4's gate-cleared Deferred item: re-enumerate the IS Polymarket universe for a recent
      past date carrying `clob_token_ids`, then re-run the `book_snapshot_5` batch backfill and verify `row_count>0`.**
      The batch path is code-complete + live-proven (live `book_snapshot_5` already captures end-to-end); only a BATCH
      row-capture proof is missing because historical IS parquets (≤2026-06-22) predate the `clob_token_ids` column and
      same-day dates are batch-future-rejected by the T-1 rule. Fix: re-enumerate the IS Polymarket universe for a
      recent past date (e.g. the most recent date ≤ today-1 with a stable IS snapshot) so its `instrument_availability`
      parquet carries populated `clob_token_ids`, THEN re-run the `book_snapshot_5` batch backfill for that date and
      confirm `row_count>0` via a manifest read. This item was ALREADY named as ready in
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s own "Deferred — gated on a sibling todo landing" section
      (verbatim: "Re-enumerate the IS POLYMARKET universe for a recent past date → re-run the `book_snapshot_5` batch
      backfill → verify `row_count>0`"), held back only pending batch4's own todo #1 (POLYMARKET instrument-lifecycle
      bounds) — that gate shipped 2026-07-28 (`instruments-service@3617261f`), confirmed live via
      `prediction_live_clob_depth_capture_2026_07_24.md`'s own 2026-08-07 finalize-reconciled Progress Log entry
      ("Reconciled 2026-08-07 (finalize P1)... that gate has now cleared... yet the re-enum+backfill itself has NOT been
      dispatched/run"). Grepped batch4/6/7/8/9 + all 5 finalizes + all 4 Phase A-E children + the consolidated closeout
      for `book_snapshot_5`/"DEFERRED-CROSS-DEP"/`clob_token_ids` immediately before drafting this todo: the only other
      `book_snapshot_5` hits are unrelated (batch7's `available_at`-consumer-check todo, already closed;
      `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`'s broader all-green MVP-backfill gate, still blocked
      on upstream A-D — not this narrower row-proof). Repos: instruments-service (re-enumerate) + deployment-service
      (re-launch the enumeration + backfill). Source: `prediction_live_clob_depth_capture_2026_07_24.md` (its own
      "DEFERRED-CROSS-DEP" checkbox, verbatim) + `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s Deferred
      section (same item). **Done when**: a manifest read confirms `row_count>0` for `book_snapshot_5` on the
      re-enumerated date, and `prediction_live_clob_depth_capture_2026_07_24.md`'s "DEFERRED-CROSS-DEP" checkbox is
      flipped `[x]` citing the evidence.

- [ ] [BACKEND] P3. **Audit + fix the SAME CQG-bundling path-resolution gap in `base_prediction_adapter.py`'s
      `_load_market_lifecycle_for_date` FALLBACK path (adjacent finding from todo 1's investigation, 2026-08-10).**
      While executing todo 1, discovered `instrument_availability_paths.py::match_instruments_blob`'s single-file
      `.../venue={V}/instruments.parquet` tail never matches instruments-service's CQG-bundled write shape (live since
      R2 2026-07-21, `process_write.py::_write_prediction_venue`) — every date since then silently resolved ZERO
      clob_token_ids via `load_polymarket_instruments_df`. Fixed for that call site (`mtds@82ba5399` — added
      `resolve_prediction_instruments_blobs`, lists + merges every `canonical_question_group=*` file for the (venue,
      date)). **NOT fixed**: `base_prediction_adapter.py:329`'s `_load_market_lifecycle_for_date` FALLBACK branch still
      calls the old single-file `resolve_instruments_blob` directly — same latent blind spot, scoped out of todo 1
      because it's a FALLBACK only reached when the PRIMARY `market_lifecycle/by_canonical_group/` read yields nothing
      (which appears to be the common case in practice — unverified whether this fallback is ever actually hit live).
      Work: (1) determine whether the fallback is ever exercised in practice (check logs/telemetry, or add a temporary
      counter); (2) if yes, switch it to the CQG-aware resolver (mirror `load_polymarket_instruments_df`'s fix) or
      generalize `resolve_prediction_instruments_blobs` for reuse there; (3) add a regression test analogous to
      `test_matches_every_cqg_bundle_for_the_venue`. Repo: market-tick-data-service. **Done when**: the fallback path is
      confirmed either dead (never exercised — document why, no code change needed) or fixed + tested to match the
      CQG-bundled shape.

- [ ] [DATA] P2. **Kalshi historical `OTHER`-bucket CQG reclassify backfill, now declassified from an operator/architect
      call to an ordinary AO-dispatchable script.** `prediction_capture_incident_remediation_2026_07_06.md`'s Phase 6
      CODE fix (`instruments-service@e0f7aaad`, `prediction.py:95`'s ticker-extraction bug) has been live 9+ days; every
      Kalshi row captured 2026-07-12 through the fix's ship date fell to `canonical_question_group=OTHER` due to the
      now-fixed bug. This was explicitly declassified from "operator/architect call" via
      `round5-cefi-question-     resolution 2026-08-08`, citing `/codex/02-data/data-pipeline-correctness-hard-rule.md`
      ("fixed in FULL, no deadline deferrals") — accepting forward-only correctness for an already-diagnosed,
      already-measured mis-bucketing is the incomplete-fix pattern that rule exists to prevent — plus `task_template.md`
      finding T/U's self-service reversibility path: a fresh same-run check (2026-08-08, re-verify before executing
      since this is a NEW run) of
      `gcloud storage buckets describe gs://market-data-tick-pred-prd-central-element-323112     --format="value(softDeletePolicy.retentionDurationSeconds)"`
      must show `>= 604800`. Work: (1) **first re-measure the real affected date range and row count from the live
      manifest** — do not trust the ~30-day/~9,500-rows/day estimate in the source doc blindly, it may have drifted
      since 2026-08-08; (2) **backup the affected manifest partition(s) before any mutation** (this is a content-patch
      of EXISTING captured rows, not a fresh write — no GCS object is deleted, but existing `canonical_question_group`
      values are overwritten in place, so a pre-mutation backup is the safety net, mirroring the reclass-script pattern
      already used elsewhere in this corpus); (3) run the now-fixed `_extract_prediction_canonical_group` classification
      logic against every backed-up `OTHER`-bucketed Kalshi row in the affected window and patch the
      `canonical_question_group` field in place; (4) verify: a post-patch distribution check shows the affected window's
      `OTHER` share back to the normal noise floor (not the near-100%-of-day mis-bucketing the source doc measured).
      Repo: instruments-service. Source: `prediction_capture_incident_remediation_2026_07_06.md` (Phase 6's second
      checkbox, verbatim — "assess whether the historical OTHER-bucketed Kalshi rows... are worth a one-off
      backfill/reclassify pass," RESOLVED to "do the reclassify" 2026-08-08). **Done when**: the backup exists, the
      affected window's rows are reclassified out of `OTHER` per the fixed classifier, the post-patch distribution check
      is recorded, and the source doc's Phase 6 checkbox is flipped `[x]` citing the evidence.

- [x] ✅ [BACKEND] P2. **Delete Polymarket's dead `_cross_reference_fixture()` capability**, per operator ruling (see
      `issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md`) (2026-08-07, option A — prediction markets
      should get fixture availability from the canonical manifest/GCS-objects path via the already-shipped
      `PredictionFixtureResolver`, not direct API-Football calls). Delete
      `PolymarketReferenceDataAdapter._cross_reference_fixture()` + `_fixture_cache` + the `api_football_api_key`
      constructor param + `factory.py`'s `af_key` threading + the dedicated `TestCrossReferenceFixture` test class.
      Grepped the full 15-doc covering set for `_cross_reference_fixture`/`api_football_api_key` immediately before
      drafting: the only hit is `prediction_phase_ab_residuals_2026_07_24.md`'s already-`[x]`-closed A5 todo, which
      explicitly declined to fix this inline ("genuine judgment call... not auto-resolved") — the operator ruling that
      resolved that judgment call postdates it and has not yet been executed anywhere. Repo: instruments-service.
      Source: `issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md` (its own sole todo, verbatim). **Done
      when**: the named methods/params/test class are deleted, `quality-gates.sh` is green, and the source doc's
      checkbox is flipped `[x]` citing the commit SHA. **DONE — instruments-service@4b55c57b.** Deleted
      `_cross_reference_fixture()`, `_fixture_cache`, the `api_football_api_key` constructor param, `factory.py`'s
      `af_key` threading, and `TestPolymarketCrossReferenceFixture` (the dedicated test class). `quality-gates.sh` green
      (`.qg_last_passed_sha=4b55c57b3ecf51c587441e7017c9c34b992803d0`); verified on origin/live-defi-rollout.

- [ ] [BACKEND] P2. **Delete the dead live-REST-polling interface on the Kalshi + Polymarket MTDS adapters**, per the
      same 2026-08-07 operator ruling (option A) applied to the sibling market-tick-data-service finding: prediction
      markets get market/price data from the canonical manifest/GCS-objects batch path, not a live-polling REST
      interface. Delete
      `KalshiAdapter.{parse_market,parse_trade,parse_order_book,normalize_market,normalize_odds,     _load_tickers_from_gcs}` +
      `PolymarketAdapter.{get_markets,get_prices,_convert_gamma_market,     _build_order_book_record,parse_market,parse_token,parse_order_book,normalize_market,normalize_odds,     _load_condition_ids_from_gcs}`
      and their dedicated tests. Grepped the full 15-doc covering set for
      `_load_tickers_from_gcs`/`_load_condition_ids_from_gcs` immediately before drafting: zero hits anywhere. Repo:
      market-tick-data-service. Source: `issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md` (its
      own sole todo, verbatim). **Done when**: the named methods and their dedicated tests are deleted,
      `quality-gates.sh` is green, and the source doc's checkbox is flipped `[x]` citing the commit SHA.

## Deferred — the other 4 orphaned docs from this run, correctly NOT extracted

Full per-doc reasoning in `issues/ag_closeout_audit_prediction_parked_2026_08_09.md`; summarized here per the skill's
non-batchable taxonomy:

- **Too-large-or-risky-for-a-batch-todo**: `data_completion_prediction_2026_07_15.md`'s Phase-B OBJECT-layer CQG-bundle
  migration (5 chained items: writer change across 3 repos, historical rollup script, drain+walk, post-verify, legacy
  delete). Confirmed un-started and uncovered; independently re-triaged to "needs its own dedicated plan" by 5 separate
  prior audit passes (batch1/2/3/4/6) — this is the 6th. Not re-drafted here again; flagging in the parked-findings doc
  as a recurring gap worth direct operator attention, since 6 audits agreeing without anyone authoring the dedicated
  plan suggests the punt itself may need a nudge, not just another re-confirmation.
- **Operator-gated (judgment call, not re-resolved by this run)**:
  `issues/ag_closeout_audit_prediction_parked_2026_07_31.md` Finding 1 — the (A) delete vs (B) keep-and-document choice
  on 2 OTHER adapter dead-code capabilities (not the 2 extracted above, which already have their own rulings). Still
  self-declared "not adjudicated," 5 audits running.
- **Time-gated (external cross-tranche dependency)**: `predictions_ml_walk_forward_and_arb_2026_06_20.md`'s 4 P0/P1
  items, chained on `sports_master:Group E` (confirmed still unchecked live). Not AO-dispatchable until that external
  gate clears.
- **Belongs to a different tranche**: `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s `[OPS] P2`
  tarball-overwrite-race item — a design choice not yet resolved to one approach, already flagged by
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s own Deferred section as `infra`/`ci`-tranche scope, not
  prediction's. Also NOT extracting that same doc's `[DESIGN] P1` fixture-pairing residual — batch9's own Deferred
  section (drafted earlier today) already treats it as claimed by
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s `[DATA] P2` "team-name alias tables" todo; flagged in this
  run's parked-findings doc as worth one more verification pass (the shipped fix's own text scopes narrower than the
  full 3-part residual it's credited with closing), but not re-litigated a 4th time here.

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — Phase 3 dispatch-scope eligibility test + conflict-check
  protocol this batch applied.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3 — the shared conflict-check
  protocol.
- `/codex/02-data/data-pipeline-correctness-hard-rule.md` — the "fixed in FULL" justification for todo 2.
- `plans/active/task_template.md` findings T/U — the self-service reversibility path todo 2 cites.

## Progress Log

- 2026-08-09 (ag_closeout_auditor, slot 14, dispatch agt-465129): drafted alongside its finalize twin, following the
  scheduled `/ag-closeout-audit prediction` run's Phase 1 (37-agent Workflow, 0 errors) and Phase 3 (conflict-check
  against the full 15-doc covering set, re-verified via fresh grep immediately before drafting — not assumed from the
  Phase-1 agents' own grep alone). 4 conflict-clear todos extracted from 4 different source docs, all previously blocked
  and all blockers cleared 2026-08-07/08. `status: draft` — awaiting operator approval to dispatch.

- 2026-08-10 (slot 31, data_engineering, todo 1 in progress — checkpoint before compact, work continues this session):
  Dispatched todo 1 (`prediction_satellite_ao_dispatch_batch10-2fff5bf2a6b4`). Found + fixed TWO independent bugs that
  were silently blocking the row-proof, both shipped + verified on origin:
  1. **CQG-bundling path-resolution gap** (`mtds@82ba5399`, `instrument_availability_paths.py` +
     `_polymarket_helpers.py`): instruments-service's prediction writer bundles `instrument_availability` per
     `canonical_question_group` (live since R2 2026-07-21) — one date/venue = N files, not one. The existing single-file
     resolver's tail-match never matched this shape, so `load_polymarket_instruments_df` silently resolved `None` for
     every date written since 2026-07-21 (not just the pre-clob_token_ids historical dates the todo's own text assumed).
     Added `match_prediction_instruments_blobs`/`resolve_prediction_instruments_blobs` (list + merge every CQG file),
     switched the Polymarket loader to use them. 4 new unit tests.
  2. **`clob_token_ids` parquet ndarray-vs-list bug** (`mtds@82ba5399` also, `polymarket_adapter.py`): found only AFTER
     shipping fix 1 and re-running the backfill VM — it STILL captured 0 rows. `_load_token_ids_from_gcs`'s
     `isinstance(raw_tids, list)` check never matches the `numpy.ndarray` a `list<string>` parquet column round-trips
     to, so every row's token-ids were silently dropped even once the file resolved correctly. Fixed via the same
     duck-typed `hasattr(x, "__iter__")` check `_is_universe.py`'s already-proven-correct live path already uses. 1 new
     unit test. A THIRD, smaller issue (file-length QG gate, 907>900 lines) required a same-session follow-up commit
     (`mtds@0a6ad2de`) to trim the added comments before it would ship. Live-verified against 2026-08-08 IS data both
     times: 173,415/182,369 rows now resolve non-null `clob_token_ids` across 65 canonical question groups (was 0 before
     either fix). Filed the SAME-CLASS residual gap in `base_prediction_adapter.py`'s lifecycle-fallback path as a new
     todo above (adjacent finding, not fixed inline — scoped out because it's an unverified-whether-ever-hit fallback
     branch, not this todo's row-proof path). **In flight at checkpoint time**: re-launched the `book_snapshot_5` batch
     backfill VM (`mtds-prediction-polymarket-20260810-014848`, zone `asia-northeast1-c`) for date `2026-08-08` with
     BOTH fixes baked into the tarball (`mtds-code@82ba53997df5` confirmed fresh at launch) — VM was `RUNNING`, log not
     yet written (early boot) as of this checkpoint. **Next step for whoever resumes**: check
     `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-prediction-polymarket-20260810-014848/run.log`
     for a terminal `command exited rc=0` + a `book_snapshot_5 tokens` capture count; if `>0`, verify via manifest read
     (`market-data-tick-pred-prd-central-element-323112`, date=2026-08-08, venue=POLYMARKET, data_type=book_snapshot_5,
     `row_count` column) and flip both this todo's checkbox AND `prediction_live_clob_depth_capture_2026_07_24.md`'s
     "DEFERRED-CROSS-DEP" checkbox citing the evidence; if the VM shows 0 rows again or a new error, diagnose fresh
     (don't assume the same 2 bugs — verify against the actual log). **Operational note (uncertain, not confirmed as a
     real bug)**: repeatedly hit this session's `run_in_background` Bash tool reporting a QG/backfill process as
     `killed` while the underlying OS process (confirmed via `/proc/<pid>/cwd`) kept running for minutes afterward on
     this shared, heavily-contended host (9+ concurrent `quality-gates.sh` instances observed across slots at one point)
     — switching to foreground `bash ... > file.log 2>&1; echo EXIT=$?` calls got a clean, trustworthy result every
     time. Not filed as an issue doc — insufficient evidence this is a reproducible harness bug vs. transient host
     contention; flagging here so a recurrence is faster to recognize.

## Deferred work — migrated to:

- N/A — the `DEFERRED-CROSS-DEP` token above (todo 1) is a citation of
  `prediction_live_clob_depth_capture_2026_07_24.md`'s own deferred checkbox, not a deferral owned by this doc; this
  plan's own todo tracks completing that item, not deferring further work. See that doc's own Deferred section for the
  live tracking.
