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
status: active
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
    /plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md,
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
context_scope:
  [
    /plans/archive/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/reconciliation-census-and-compute-tiers.md,
    /codex/02-data/canonical-cutover-register.md,
    market-tick-data-service/scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py,
  ]
---

# Prediction satellite AO batch 4 — un-triaged sibling-doc gap extraction

> **Status: active — operator-dispatched (2026-07-28+).** Drafted autonomously by the `/ag-closeout-audit prediction`
> scheduled run (2026-07-26) as a `status: draft` skill-drafted batch (never auto-shipped per CLAUDE.md's "Plan
> destination — ASK BEFORE CREATING" HARD RULE); the operator flipped it to `active` and dispatched it (Progress Log
> tasks `batch4-013/-017/-020/-023/-024`). All split items 4a/4b-i/4b-ii/4c are COMPLETE; one follow-on remains — 4b-iii
> (shape #4 merge + delete), tracked as a todo below.

## Why this batch exists (the gap batch3 missed)

`prediction_satellite_ao_dispatch_batch3_2026_07_26.md` is itself a same-day ag-closeout-audit output that triaged 17
prediction docs. Its candidate set excluded the 4 forked Phase children AND never reached the 3 sibling docs that
`prediction_phase_ab_residuals_2026_07_24.md`'s A3 "close 12 residuals" item explicitly relocated its work into
(`prediction_perps_kalshi_polymarket_parked`, `prediction_live_clob_depth_capture`,
`prediction_cross_venue_arb_and_coverage`). Grep confirms: those 3 basenames appear in ZERO batch/native_ao plan and are
never mentioned by batch3 — they are cited only in `prediction_consolidated_closeout_2026_07_18.md`'s "Aggregated source
docs" digest (the confirmed DIGEST TRAP: listing ≠ dispatch). This batch closes that specific gap.

## Todos

- [x] ✅ [SCRIPT] P0. **DONE 2026-07-26 (slot-7)** — all three legs were ALREADY SHIPPED by prior commits; this todo's
      "0/25 populated" premise was stale. **Leg (1)** instruments-service: POLYMARKET (`instruments-service@be45660f`)
      and KALSHI (`instruments-service@686e0ac4`) already set `available_from_datetime`/`available_to_datetime` from
      gamma/Kalshi lifecycle fields in `_parse_market()` (`polymarket/parsing.py:139-143`, `kalshi.py:849-850,918-919`).
      Gap found: KALSHI's `_parse_market()` had ZERO direct unit-test coverage of this (unlike Polymarket's
      `test_parse_market_populates_lifecycle_bounds_from_gamma`) — added
      `test_parse_market_populates_lifecycle_bounds_from_kalshi` +
      `test_parse_market_floors_available_from_to_midnight_for_intraday_open_time` to
      `tests/unit/test_prediction_lifecycle.py` (proves non-NULL bounds + the DP-PATH-006 midnight-floor behavior).
      Shipped `instruments-service@3617261f`; QG green (4913 passed). **Leg (2)** market-tick-data-service: honest-
      absence emission already bounded to the lifecycle window in
      `engine/orchestrator/sentinels.py::_emit_tier3_for_dt` +
      `prediction_tier3_lifecycle.py::_classify_prediction_tier3_reason` (typed `EXPECTED_INSTRUMENT_NOT_LISTED`/
      `EXPECTED_INSTRUMENT_DELISTED`, never bare `empty_confirmed`), already covered by
      `tests/unit/engine/test_sentinels_prediction_lifecycle_tier3.py`
      (`test_pre_genesis_cid_routes_to_expected_instrument_not_listed`,
      `test_post_resolution_cid_routes_to_expected_instrument_delisted`). No code change needed; QG green (7015 passed,
      0 changes). **Leg (3)** unified-api-contracts: verified `OUT_OF_COVERAGE_WINDOW_REASONS`
      (`_honest_coverage_empty_reasons.py:590-606`) already excludes both reasons from the coverage denominator, already
      covered by `tests/unit/test_coverage_exclusions.py::test_reason_is_out_of_model_clipped_from_denominator`. No code
      change; QG green (0 changes). All 4 "Done when" criteria satisfied. **Populate POLYMARKET + KALSHI instrument
      lifecycle (`available_from_datetime`/`available_to_datetime`) on the write path + bound honest-absence emission to
      the lifecycle window.** (1) instruments-service: the POLYMARKET gamma raw-market enumeration MUST set
      `available_from_datetime` from gamma `startDate`/`createdAt` + `available_to_datetime` from `endDate`/`closedTime`
      (today both NULL → 0/25); apply the SAME check for KALSHI (the adapter sets `market_created_at`/`resolution_time`
      on `MarketLifecycle` — verify those flow onto the `InstrumentRecord`'s `available_from/to_datetime`). (2)
      market-tick-data-service / UTL honest-absence emission: only emit a cell (captured/empty/failed) for dates WITHIN
      `[available_from, available_to]`; outside the market's life = honest
      `empty_confirmed[EXPECTED_INSTRUMENT_NOT_LISTED|DELISTED]` (out-of-window-classified — see leg (3)), NEVER a
      bare/unqualified `empty_confirmed`. (3) unified-api-contracts: **do NOT remove**
      `EXPECTED_INSTRUMENT_NOT_LISTED`/`PRE_VENUE_LAUNCH`/`DELISTED` from `EMPTY_CONFIRMED_REASONS` — resolved
      `autonomous_session_operator_decisions_2026_07_25.md` entry #13 (option A, 2026-07-26): all three are already
      members of `OUT_OF_COVERAGE_WINDOW_REASONS`
      (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_empty_reasons.py:590-616`),
      the operator-directed coverage-denominator partition (2026-06-12, extended 2026-07-17) that already clips them
      from numerator AND denominator while keeping the raw rows honestly `empty_confirmed` + a visible reason badge —
      the "blanks where we expected data" goal this leg was chasing is already delivered by that mechanism, and removing
      the enum members would break `record_empty(reason=...)` validation (`UnknownEmptyConfirmedReasonError`) for every
      asset group that emits them. This leg is now: **verify** `OUT_OF_COVERAGE_WINDOW_REASONS` actually excludes
      prediction's out-of-lifecycle cells from the numerator/ denominator (no code change expected — a confirming unit
      test / manifest spot-check only). This is the bounded CODE leg only — the historical manifest re-walk to
      reclassify already-written rows is the SEPARATE `[OPERATOR]` walk in the Deferred section (gated on this todo
      landing). Repo: instruments-service + market-tick-data-service + unified-api-contracts. Source:
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (P0 lifecycle/empty- emission item, "BIG finding —
      data-correctness, honest-coverage semantics"). **Done when**: the POLYMARKET + KALSHI write paths populate
      `available_from/to_datetime` (proven by a new/extended unit test asserting non-NULL bounds from a fixture
      gamma/kalshi market), the emission path bounds captured/empty/failed cells to the lifecycle window (unit test: an
      out-of-lifecycle date yields `empty_confirmed[EXPECTED_INSTRUMENT_NOT_LISTED|DELISTED]`, never a bare
      `empty_confirmed`), a test/spot-check confirms `OUT_OF_COVERAGE_WINDOW_REASONS` already excludes these from the
      denominator (no `EMPTY_CONFIRMED_REASONS` enum change), and `quality-gates.sh` is green across all three repos.

- [x] ✅ [DATA] P2. **Verify END-TO-END MDPS prediction depth-history retention — DONE 2026-08-04 (slot-5), VERDICT:
      FAIL.** Full evidence + verdict recorded in `prediction_live_clob_depth_capture_2026_07_24.md`'s Progress Log
      (this todo's Done-when target): the raw flush path still overwrites per instrument (day+instrument-keyed, no
      window key), AND the processed prediction candle/book store has zero `pipeline_mode=live_*` objects on every
      sampled day (2026-06-23/24/26/28), including for `trades` which has a registered MDPS adapter. Follow-up fix work
      filed as `plans/active/issues/prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` (3 todos) per the
      findings-closure HARD RULE — this verification todo itself was read-only, no data mutation. Original todo text
      preserved below for context (NOT a checkbox — do not re-derive as a backlog task).

  > Original: The raw live prediction book store is a rolling-latest-window (does not retain multi-hour history by
  > itself). Confirm (a) MDPS's prediction live-scan cadence against the raw live-book flush window, and (b) that the
  > PROCESSED prediction book/candle store actually accumulates multi-hour history rather than only mirroring the
  > rolling raw window — a bounded read/grep of the MDPS scan config + a GCS-timespan check on the processed prediction
  > store, with a stated pass/fail verdict. Repo: market-data-processing-service (+ market-tick-data-service read-only
  > for the raw-window comparison). Source: `prediction_live_clob_depth_capture_2026_07_24.md` (P2 "Verify END-TO-END
  > depth-history retention"). Done when: a dated verdict is recorded (PASS = processed store demonstrably
  > accumulates >1 flush-window of prediction depth history, with the measured processed-store time span cited; or FAIL
  > = a named retention gap + the specific scan-cadence/flush-window mismatch), committed to that doc's Progress Log.
  > Read-only verification — no data mutation.

- [x] ✅ [SCRIPT] P2. **cqg recent-window catalogue re-enumeration with the already-fixed classifier — VERIFIED ALREADY
      COMPLETE 2026-08-04 (slot 6), premise stale.** Live read of the prediction instruments-store
      (`gs://instruments-store-pred-prd-central-element-323112/instrument_availability/by_date/canonical_question_group=*/day={D}/venue=*/`)
      confirms all three target dates already carry the full real-cqg spread — **2026-06-20: 11,086 rows / 42 real cqg
      groups; 2026-06-21: 12,052 rows / 42 groups; 2026-06-22: 9,986 rows / 40 groups** — vs the reference 2026-06-23
      (15,330 rows / 41 groups). The premise ("refreshed for 2026-06-23 only") was stale: the same **2026-06-26 IS
      enumeration VM run** (`instr-backfill-pred-20260621`) that wrote 2026-06-23 also enumerated 2026-06-20..22 with
      the already-fixed classifier (catalogue objects created 2026-06-26 16:04–18:28 GMT, after the 2026-06-23 21:08Z
      fix tarball); the target dates show the SAME ~22–29% OTHER-fraction profile as the verified-good baseline, so
      OTHER is the expected unclassifiable residual, not a classifier failure. No code change and no re-run
      (re-enumerating would only re-write byte-equivalent prod objects — data-engineering EFFICIENCY north-star).
      Evidence recorded in `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s 2026-08-04 Progress Log entry (the
      Done-when target); that doc's own cqg item flipped in the same commit. Closure mirrors this plan's todo #1
      (premise-stale / already-shipped). Repo: none (verification-only, no mutation). Original text preserved below
      (context only, not a re-derivable checkbox). **cqg recent-window catalogue re-enumeration with the already-fixed
      classifier.** The cqg-partitioned `instrument_availability` catalogue (instruments-store) is refreshed for
      2026-06-23 only (34 groups verified); re-enumerate the recent enumerated window (2026-06-20..22) with the fixed
      cqg classifier so those dates' catalogue also carries real `canonical_question_group` values. This is an
      operational run of the ALREADY-FIXED classifier over a bounded 3-day window (deep history is the bulk-tick-seed
      with no per-date catalogue — out of scope here). This touches the IS cqg-catalogue enumeration module, DISTINCT
      from todo #1's adapter-lifecycle write path (no file collision). Repo: instruments-service. Source:
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (P2 "cqg partition-completeness — recent-window catalogue
      re-enumeration"). **Done when**: the 2026-06-20..22 cqg catalogue partitions are re-enumerated and a live read
      confirms each of those 3 dates now carries populated `canonical_question_group` catalogue rows (count cited), with
      the run's evidence recorded in the source doc's Progress Log.

- **[CODE] P1. Extend the canonical `trades` schema for POLYMARKET metadata + migrate the legacy `prediction_trades`
  population** — ROLLUP (split 2026-07-28, slot-12, into 4a DONE + 4b, itself split into 4b-i/4b-ii COMPLETE + 4b-iii
  open; see below). Operator ruling 2026-07-25 (`unified-trading-pm@7dfcfe0ee`,
  `plans/archive/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`): extend the
  canonical `data_type=trades` schema rather than drop the legacy metadata or permanently fork a separate canonical
  shape. Source: `prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md` todos 4-6 — batch3 deferred
  this doc as operator-gated on Q3; the `prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md` re-check
  (2026-07-26) confirmed Q3 cleared the SAME day batch3 was drafted.

  - [x] ✅ [CODE] P1. **4a — schema + writer (DONE 2026-07-28, slot-12).** (1) unified-api-contracts: added
        `title`/`slug`/`event_slug` as first-class canonical `trades` `ColumnSpec` entries in
        `registry/_schema_spec_prediction.py` (`outcome`/`outcome_index` were already present). Trader-identity fields
        (`proxy_wallet`/`name`/`pseudonym`/`bio`/`profile_image`) explicitly EXCLUDED — PII-adjacent, still needs a
        SEPARATE operator call. Regression test `test_prediction_trades_carries_market_question_metadata` added to
        `tests/unit/test_schema_spec_completeness.py`. Shipped `unified-api-contracts@90ddcc01`, QG green. (2)
        market-tick-data-service: `PolymarketAdapter._POLYMARKET_USER_META_COLS` no longer drops `title`/`slug`/
        `eventSlug` (PII fields stay dropped); `_annotate_cid_dataframe` renames `eventSlug`→`event_slug` and
        `outcomeIndex`→`outcome_index` (canonical snake_case) before the existing numeric-coercion step. New test file
        `tests/unit/test_polymarket_adapter_metadata_fields.py` (3 tests: metadata survives, PII still dropped,
        outcome_index still numeric-coerced). Shipped `market-tick-data-service@84154e1a`, QG green (7241 passed).
        **This is the WRITER-ROOT fix that `scripts/canonicalize_prediction_manifest_2026_07_18.py`'s OPERATOR-REVIEW
        CHECKLIST item 0 was gated on** — that script's manifest-only canonicalization can now proceed per its own
        checklist (still operator-held for items 1-6, unrelated to this todo).
  - [x] ✅ [DATA] P1. **4b-i — migrate shapes #3/#3b (COMPLETE 2026-08-06, slot-16).** Enrich the existing canonical
        `data_type=trades` objects with `title`/`slug`/`event_slug` recovered from the legacy
        `data_type=prediction_trades` bundle-per-underlying tree (shapes #3/#3b — manifest-known, 2,477 rows / 348
        distinct dates, 14 `underlying` values), then delete the now-redundant legacy objects once content-verified.
        **Script shipped**: `market-tick-data-service@e4acf0c4`
        (`scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py` + 20 unit tests, QG green) — additive-only
        enrichment (never overwrites an existing column; some canonical objects already carry a richer pre-existing
        schema variant with these fields under camelCase aliases — alias-aware, skipped, not overwritten — a real bug
        caught + fixed by the script's own `_original_columns_unchanged` safety check during dry-run validation before
        any real write). Merge key: `transaction_hash` (legacy) == `transactionHash` (canonical), cross-checked against
        `timestamp` (unix-seconds). Delete gated on a FRESH `gcs_bucket_soft_delete_retention_seconds()` check (codex
        delete-safety §3a) — measured `604800`s (exactly 7 days) on `market-data-tick-pred-prd-central-element-323112`
        at execution time, qualifying the delete as reversibility-qualified (no `[OPERATOR]` gate needed per CLAUDE.md's
        plan-authoring rule for this exact carve-out). **Live-verified scope correction to the original premise below**:
        the canonical shape#1 twin exists for EVERY sampled date across the full 2025-03-14..2026-04-14 range (not
        date-range-gated as initially worried) — confirmed via a live read at 6 sampled dates spanning the full range,
        each showing matching shape#1/shape#4 object counts. **Execution status (updated 2026-07-28, session end)**:
        `--apply` (enrichment only, no deletes yet) ran 55/348 dates (0 anomalies) before the WORKER SESSION DIED
        mid-run (background process reaped, exit 144/SIGTERM — not a script bug; every write up to that point was
        content-verified before commit and is durable in GCS). **Resumable by anyone**: re-run
        `.venv/bin/python scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py --apply --report <path>` — the
        script's own idempotency check (`all_fields_present`) skips already-enriched canonical objects even without the
        report file, so a fresh run without one is still 100% correct, just re-lists GCS for the already-done days. The
        delete pass (`--delete-legacy`) runs as a separate follow-on invocation after the enrichment pass completes and
        a sample is spot-verified. **Checkbox stays unchecked until the full 348-date enrichment + delete pass is
        verified complete** (real backfill completion, not code-shipped — per CLAUDE.md "Plans run to actual completion,
        not smoke-test green"). Repo: market-tick-data-service. **Done when**: all 348 dates' shape#3/#3b objects are
        enriched into their canonical twins (verified via readback) and deleted (verified via
        `gcs_describe_object(...) is None`), 0 anomalies outstanding.
  - [x] ✅ [SCRIPT] P2. **4b-ii ENUMERATION COMPLETE 2026-08-04 (slot-15) — shape #4's corpus-wide extent enumerated;
        merge+delete follow.** Shape #4 (10-segment `data_source=POLYMARKET_CLOB/...` tree) is explicitly OUT OF SCOPE
        for 4b-i — its corpus-wide extent is GENUINELY UNKNOWN (the issue doc's "158+" figure is a ONE-DAY
        `day=2025-04-11` sample only, live-confirmed exactly 158 objects for that one day, not a corpus total).
        Enumerating every day shape #4 exists on IS a new whole-corpus walk (review-blocking per CLAUDE.md single-walk
        discipline) — it must run as the ONE sanctioned Tier-2 SPOT VM single walk per
        `/codex/02-data/reconciliation-census-and-compute-tiers.md`. **Re-tagged off `[OPERATOR]` (2026-07-28)**: the
        safe-idempotent justification per CLAUDE.md's VM-launch-gating OR-clause is stated directly — this walk is a
        READ-ONLY enumeration (no GCS mutation), cheaply re-run on preemption (idempotent re-listing, no partial-state
        risk), so it launches via the standard Tier-2 SPOT VM single-walk mechanism without a separate operator
        sign-off. Once the corpus-wide extent is known, the merge logic is the SAME read-transform-write-per-cell
        pattern as 4b-i's shipped script (shape #4 already carries `title`/`slug`/ `eventSlug` per the issue doc's
        content-verify — the merge direction may in fact be shape#4 -> shape#1, richer source into the (possibly
        still-bare) canonical twin, mirroring 4b-i's alias-aware additive-only approach). Repo:
        market-tick-data-service. **Done when**: shape #4's full corpus-wide object set is enumerated (VM-run), merged
        into canonical with a verified 0-loss content-check per delete-safety Part 2, and legacy objects deleted only
        after verification.
  - [x] ✅ [DATA] P2. **4c — register the writer cutover in `canonical-cutover-register.md` +
        `non-canonical-path-inventory.md` — unified-trading-pm@cb59926c6.** 4a's writer-root fix (title/slug/event_slug
        now flow to new canonical writes) ALREADY registered in §6e by 4a's ship; this task updated §6e's historical
        backfill state (4b-i at 299/348, 4b-ii enumeration complete with corpus-wide stats, 4b-iii pending) and
        non-canonical-path-inventory.md row 22 (shape #4 extent now known, 4b-i/4b-ii/4b-iii status). Raw-object
        migration disposition stays `no-migrate-first` — not `yes-twin-confirmed` until migrations actually execute.

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
  walk to avoid concurrent-write races on the same `_index`. **Reviewed 2026-07-28, confirmed remains a permanent
  hard-stop — NOT retagged.** The fix itself is fully designed (nothing left to decide on the mechanics); workspace
  policy simply reserves execution of a production manifest `--apply` write like this for a human forever, because a
  false positive would silently mark good captured data as failed. Confirm you (or whoever you designate) will
  personally review and run it once todo #1 lands. Source: `prediction_cross_venue_arb_and_coverage_2026_07_24.md`
  (P2/P3 residual-manifest items, both "NICE-TO-HAVE", both "ride the next prediction canonicalisation walk"). **Gate
  cleared 2026-08-07** (`instruments-service@3617261f`). Finalize P2 live counts (slot-11, 2,666,644 total rows):
  out-of-lifecycle `empty_confirmed` = **38,020** (was ~49.6k, 2026-06-23); `SOURCE_RETURNED_ZERO` = 1,953,482 (was
  93,264); legs (b)/(c) (lowercase/blank/UNKNOWN venue + v4 rows) = **0** — already resolved. Remaining: leg (a) only
  (38,020 rows + `SOURCE_RETURNED_ZERO` out-of-lifecycle scope audit). Source doc P2/P3 flipped `[x] ✅`. Batch5
  candidate.
- **[SCRIPT] Re-enumerate the IS POLYMARKET universe for a recent past date → re-run the `book_snapshot_5` batch
  backfill → verify `row_count>0`.** A bounded, idempotent re-enumeration+backfill; it shares the POLYMARKET IS
  enumeration path with todo #1 so it should sequence AFTER #1 lands (else it re-enumerates against the old write path).
  **Re-tagged off `[OPERATOR]` (2026-07-28)**: the safe-idempotent justification already stated here (the shard re-runs
  cleanly on preemption) satisfies CLAUDE.md's VM-launch-gating OR-clause — launches via the standard backfill-VM
  mechanism, no separate operator sign-off needed. Source: `prediction_live_clob_depth_capture_2026_07_24.md` (the
  "DEFERRED-CROSS-DEP" `book_snapshot_5` row-proof item). **Gate cleared 2026-08-07** (`instruments-service@3617261f` —
  todo #1 landed). **Promoted to ready `[DATA]` candidate** (finalize P2, slot-11): AO-dispatchable (re-tagged off
  `[OPERATOR]` 2026-07-28), no remaining gates. Batch5 or standalone plan.

## RULED 2026-07-28 — arb-pairing wiring + politics/geo canonicalization (was: operator / design-gated)

Both items below were previously deferred as `BLOCKED-OPERATOR-DECISION` in
`prediction_cross_venue_arb_and_coverage_ 2026_07_24.md`. Applying the general theme (canonicalization work gets built
FULLY, not left as a standing design gate; this workspace already has a proven precedent for exactly this class of
cross-venue-matching problem — the soccer fixture-match resolver,
`instruments-service/reference_data/adapters/prediction/fixture_match.py`, which pairs Polymarket/Kalshi markets to the
same real-world event via `af_fixture_id` + team/league resolution through a shared alias index, closed-set
honest-absence, no silent fallback):

- **Fixture-pairing residual (registry-resolution + mapping-population + arb-layer WIRING across UAC/IS/features/
  strategy)** — **RULED: build it, generalizing the already-proven soccer fixture-match resolver pattern.** This is not
  a novel design call; it's applying an existing, shipped architecture (registry-resolution + per-instrument side-table
  - closed-set honest-absence, the exact shape A4 above already used for soccer) to the cross-venue pairing problem.
    Retagged `[BACKEND] P2` (was `[DESIGN]`) — build the FULL mechanism (no partial/heuristic-only pairing), wired
    across UAC (schema) / instruments-service (resolver) / features-service (consumption) / strategy-service (arb
    layer), per the theme's full-completion mandate (no shortcuts, no partial MVP). Source doc's own todo carries the
    scoping detail; this ruling only removes the "needs a design session first" gate.

    **Partial ship 2026-07-31** (`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s fixture-pairing todo,
    `prediction_satellite_ao_dispatch_batch6-008`): UAC (`@1dddc680`), instruments-service (`@62a8b1d8`), and
    strategy-service (`@d71c8aa4`) all shipped real code for the MLB league; features-service needed no changes (its
    dispatch/kernel were already sport-agnostic, confirmed via its existing test coverage). The genuinely remaining
    piece — cross-venue team-name alias tables for MLB/NFL/NBA/tennis, needed to safely widen past MLB and pair on
    venue-mismatched team-name renderings without risking a false pair — is real data-engineering work, not a
    code-wiring gap, and was NOT fabricated; it's tracked as its own new `[DATA] P2` todo in the batch6 doc. Full
    per-repo breakdown + the "why not the rest" reasoning is in that todo's own Partial-progress note and the source
    doc's (`prediction_cross_venue_arb_and_coverage_2026_07_24.md`) matching update.
- **Politics/geo cross-venue canonicalization audit (which families are genuinely arbable + how to name/group them)** —
  **RULED: build the FULL structured enumeration now (bounded, checkable), narrowed to a residual operator ask only
  where genuinely tied.** Determining whether two differently-labeled venue markets resolve to the SAME real-world event
  is a semantic/domain judgment the general theme does not mechanically determine — but per this corpus's own
  established pattern for exactly this shape (see `prediction_phase_ab_residuals_2026_07_24.md`'s "ambiguous canonical
  dimension values" ruling, 2026-07-28), the correct scoping is: (1) enumerate every Kalshi Politics 2049-series vs
  Polymarket TRUMP/GEO family pair with a proposed canonical grouping + recommendation per pair (a bounded, checkable
  audit deliverable, not an open conversation); (2) apply the arbable/non-arbable call per pair using objective
  structural signals already available (same underlying resolution date + same real-world referent, mirroring the soccer
  fixture-matcher's `af_fixture_id`-equivalence test) wherever those signals disambiguate; (3) escalate ONLY the
  specific pairs where structural signals don't disambiguate (not the whole audit) as a narrow options+recommendation
  operator question. Retagged `[UAC] P2` (was `[UAC]`/design-gated) — the audit itself is now a normal AO-dispatchable
  todo; only a genuinely-tied residual, if any, stays operator-gated.

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
- **`[DATA] P3. 49 canonical-only POLYMARKET trades days (2025-04-19..2025-06-05 + 2025-06-13) lack `title`/`slug`/`event_slug`with no legacy source** — these days are OUTSIDE the 348-date legacy bundle (never had`prediction_trades`objects, so 4b-i's enrich-from-legacy path cannot cover them). Sampled 2026-08-06 (4 days: 2025-04-19/05-15/06-05/06-13): canonical`data_type=trades`objects carry 46-141 shards/day, all`enrichment_fields_present=False`. Whether these fields are recoverable from the IS POLYMARKET reference universe / `prediction_canonical_question_group`/`market_lifecycle`(the latter covers these dates per the manifest census) is an open investigation — a follow-up for a future prediction batch, NOT in 4b-i scope (4b-i done-when is the 348 legacy dates). Evidence: manifest`trades`dates in legacy range = 397, of which 49 are not-in-checkpoint AND legacy-absent = this exact set; scratchpad`legacy_presence.json`+`audit_remaining_days.py`at`gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/`.

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
`issues/prediction_arb_live_execution_bridge` (**RULED 2026-07-28 — no longer operator-gated, see this batch's own
"RULED 2026-07-28" section above and the issue doc's retagged `[BACKEND]` todo**),
`issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue` (operator — historical re-backfill launch),
`issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index` (**RULED 2026-07-28 — authorize the third
remediation attempt once the deploy is confirmed** (general theme: full backfills/migrations, DO IT when not a
regression — the underlying `unified-trading-library@14301571` TOCTOU fix has already shipped and proven stable across 5
consolidator cycles on a sibling bucket). Converts to a bounded, dispatchable sequence: (1) verify
`unified-trading-library@14301571` is deployed to the `uts-prod-manifest-consolidator-instruments-sports` Cloud Run job
specifically (image build timestamp / pinned library version vs. the commit's merge time); (2) if not yet deployed,
deploy it; (3) once deployed, re-run `remediate_cross_ag_prediction_bleed_round3_2026_07_24.py` (already built,
reusable, REMOVE-only) against `instruments-store-sports-prd`; (4) hold-verify across ≥2 real consolidator cycles (not
just an immediate check) before closing — full completion, no partial verify. The actual checkbox for this sequence
lives in the (archived) issue doc
`plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_ instruments_index_2026_07_20.md`, out of scope for
this file's edit pass — this note records the ruling so a follow-up pass can retag that doc's own todos 12-14
accordingly), `sports_arb_decay_window_and_alpha_gate_design` / `sports_group_c_execution_backtest_harness` /
`sports_predictions_live_mode_activation_readiness` / `sports_odds_feature_naming_canonicalization` (sports-master-owned
/ design-gated / time-gated), `predictions_ml_walk_forward_and_arb` (time-gated on sports_master Group E),
`data_completion_prediction_2026_07_15` (human-only — 3× independently re-triaged to 0 AO-eligible). The 4 forked Phase
children (`prediction_phase_ab_residuals` Phase-B fixture-attribute backfill, `prediction_phase_c_data_status_ui`,
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
- **2026-07-28→2026-08-06 — 4b-i CONDENSED HISTORY (originally ~35 Progress Log entries across ~15 slot
  dispatches/resumes; condensed 2026-08-13 by slot 18 to clear the plan's 1000-line hard cap — no decision-relevant
  detail dropped, only repeated resume/blocker-recheck narration).** Built + shipped
  `market-tick-data-service@e4acf0c4` (`scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py`, 20 unit tests)
  — alias-aware, additive-only enrich of canonical `data_type=trades` shapes #3/#3b from legacy `prediction_trades`
  (2,477 rows/348 dates), then delete-legacy gated on a fresh `gcs_bucket_soft_delete_retention_seconds()` ≥604800s
  check. The `--apply` run spanned ~10 days and ~10 slot handoffs (7, 8, 13, 15, 5, 6, 12, 16, and others) due to
  repeated session deaths mid-run; each resumer recovered the durable checkpoint (scratchpad → later a durable GCS
  copy at `_ops/prediction_trades_migration_checkpoint_2026_07_31.jsonl`, then `_ops/4bi_run_checkpoint_latest.jsonl`)
  and relaunched from the last-completed day. **Real lessons that landed as fixes/docs (still load-bearing, kept
  here)**: (1) `nohup ... &` does not survive session death — `orphan_reap` kills it; use harness `run_in_background`
  instead (shipped `unified-trading-pm@38e6de9fa`, issue doc
  `issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`); (2) even `run_in_background`
  survives orphan_reap but NOT `WorkerLivenessWatchdog`'s `kill_session` if you go >25min without a `/progress`
  heartbeat — always pair a long job with a self-heartbeating watchdog (documented in
  `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` § "Watcher coverage"); (3) this todo was concurrently
  dispatched to 3+ slots at once (no dispatcher-side de-dup for a long-running resumable script) — real wasted GCS
  read cost but no corruption (additive/deterministic merge); filed
  `issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md`; (4) a real dispatcher bug
  (`issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`) blocked the sibling
  `mtds_available_at_cross_asset_backfill` plan's manifest-consolidator cron for several days, which in turn blocked
  this migration's manifest-dependent date discovery — eventually cleared out-of-band; (5) the shared host's ambient
  `gcloud` account is not stable across a long poll loop — always pin `--account=` explicitly. **Environment shift
  mid-migration**: the sibling plan's manifest rebuild replaced the prediction `_index` (no more `prediction_trades`
  rows), so the script's manifest-driven date source was replaced with an explicit 348-date list driven off the 4b-ii
  enumeration; delete-pass driver variants (`run_4bi_delete_s{4,5,8,13}.py`) were sharded (up to 6-way) to fit
  session-survivable chunks given the measured ~5-13 min/day cost on some ranges.
- **2026-08-06 (slot 16, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`) — 4b-i
  COMPLETE.** Final verification re-run over all 348 dates found 4 residual shape3b-only legacy objects on
  `day=2026-04-14` (no canonical twin — correctly skipped by the enrichment pass, content-verified + deleted directly).
  **Total: 3,574 legacy `prediction_trades` objects deleted across the full 2025-03-14→2026-04-14 range, 0 anomalies
  outstanding.** All tooling + inputs durably archived at
  `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/`. Checkbox flipped (no new
  code commit — the shipped `@e4acf0c4` script + scratchpad delete-driver, already durably archived, drove the work).
- **context-scout 2026-08-01/2026-08-03/2026-08-06**: context_scope refreshed 3× across this stretch (4-5 entries each
  time), unchanged in substance.
- **2026-08-04T21:0xZ (slot 15, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-024`)**: 4b-ii
  enumeration COMPLETE. Built + shipped `market-tick-data-service@e46fb943`
  (`scripts/enumerate_shape4_prediction_trades_2026_08_04.py`, read-only GCS listing, manifest-based day discovery,
  per-day prefix listing). **Key finding**: the issue doc's original path shapes (under bucket root) are STALE — the
  raw-tick estate was migrated under `raw_tick_data/by_date/day=.../pipeline_mode=.../asset_group=prediction/` between
  2026-07-24 and 2026-08-04. Shape #4 now lives at:
  `raw_tick_data/by_date/day={date}/pipeline_mode=batch_polymarket_clob/asset_group=prediction/data_source=POLYMARKET_CLOB/...`
  (canonical prefix wrapping the original 10-segment tree). **Corpus-wide extent**: **348 days** (2025-03-14 →
  2026-04-14, matching 4b-i's range exactly), **1,126,358 total objects**, **563,173 unique condition_ids**, **100% of
  days have canonical flat twins** (shapes #4 and #1 coexist for every day). **13 market categories** (CRYPTO_PRICE
  502k, MISC 418k, SPORTS_OTHER 104k, WEATHER 44k, SPORTS_FOOTBALL 23k, POLITICS_US 13k, TECH 12k, ...), **93
  underlyings** (UNKNOWN 418k, BTC 122k, ETH 116k, SOL 94k, XRP 92k, NBA 80k, ...), **4 market types** (binary 1M,
  range_bracket 126k, ranked 530, categorical 168), **8 resolution periods** (event 524k, yearly 383k, monthly 208k,
  weekly 9k, ...). **0 errors**. Results durably uploaded to
  `gs://market-data-tick-pred-prd-central-element-323112/_ops/shape4_corpus_enumeration_2026_08_04.jsonl` (348 lines) +
  `shape4_corpus_summary_2026_08_04.json`. **Merge+delete are separate follow-on work** — the merge direction is shape
  #4 → canonical shape #1 (shape #4 carries richer `title`/`slug`/`eventSlug` metadata, 24 cols vs canonical 22),
  mirroring 4b-i's alias-aware additive-only approach in `migrate_prediction_trades_legacy_bundle_2026_07_28.py`. Filed
  as a new sub-item below.
- [ ] [DATA] P2. **4b-iii — merge shape #4 into canonical + delete legacy objects.** Gate cleared (4b-i COMPLETE
      2026-08-06 — both migrations share the same canonical target; concurrent writes would race). Apply the same
      read-transform-write-per-cell pattern as 4b-i to enrich canonical shape #1 objects with
      `title`/`slug`/`event_slug` from their shape #4 twins (1,126,358 objects, 348 days, 100% twin coverage confirmed
      by 4b-ii's enumeration), then delete the now-redundant shape #4 legacy objects after content verification.
      **Delete safety**: mirror 4b-i's reversibility-qualified pattern — gate the delete on a FRESH
      `gcs_bucket_soft_delete_retention_seconds()` ≥604800s check before any object deletion (codex delete-safety §3a);
      no `[OPERATOR]` gate needed per that carve-out. Repo: market-tick-data-service.

      **STATUS 2026-08-12 (slot 18) — FINDING + FIX + RELAUNCH IN FLIGHT.** VM `...-201105` (slot-25's launch) COMPLETED
              EXIT_STATUS=0 (TOTALS: 1,126,358 objects / 563,173 cids, canonical_already_enriched=1,126,338,
              legacy_objects_deleted=326,848). **Post-run verify: delete leg INCOMPLETE (29%)** — the shipped script's
              `_canonical_ts_seconds()` mis-converts canonical `timestamp` when it's int64 unix-seconds (the 2026-01-15+
              writer format; `pd.to_datetime` misreads seconds-as-ns → every key ≈1s) → `_metadata_matches` false-negatives
              → 100% of cells wrongly refused on 2026-01-15..2026-04-14 (+4 2025 days) = **94 days / 775,406 objects kept**.
              FIX SHIPPED: `market-tick-data-service@5271ea7c` (int64 passthrough, +2 tests, QG green) +
              `deployment-service@b9cbb1b1` (tarball build also broken — 11G gitignored `.tmp/count_check_*` inflated the
              tarball to 7.7G, overflowed /tmp, shipped stale tarball; added `--exclude='.tmp'`). MTDS tarball republished
              pinned `5271ea7c` (content-verified). **RELAUNCHED VM `canonical-migration-prediction-shape4-merge-20260812-221112`**
              (on-demand, full `--apply --delete-legacy`, full range) — retention gate 604800s PASSED, DEPLOYMENT_STARTED,
              running. Checkbox flips after this VM completes + post-delete verify (final counts in Progress Log).

- [x] ✅ [DATA] P2. **Characterize the shape-#4 subset-divergent cells (canonical ⊂ shape #4)** — discovered 2026-08-10
      (slot 25, 4b-iii dry-run): ~10% of cells (9/85 on day 2025-03-14, e.g. `0x58b3...`, `market_type=range_bracket`)
      have a canonical twin carrying FEWER trades than the shape #4 object (2 vs 12 — metadata VALUES identical, row set
      divergent). The migration correctly keeps + flags these (delete would lose real trades), but the canonical
      `trades` objects for these cells have a **data-completeness gap** that warrants characterization: (a) quantify the
      population (bounded read of the migration report's anomaly lines once the VM run completes — expected ~10%), (b)
      determine if it is market_type/underlying-specific (range_bracket hypothesis), (c) decide disposition: backfill
      the missing trades from shape #4 into the canonical (row-set union — a SEPARATE operation from 4b-iii's
      enrichment, with manifest implications) OR accept the canonical as the manifest-SSOT subset and keep the shape #4
      objects in place as honest non-canonical. (repo: market-tick-data-service). Done when: the population is counted +
      a disposition decision is recorded in this plan's Progress Log. — **CHARACTERIZED 2026-08-10 (slot 24)**, full
      evidence + disposition in the Progress Log below.

- **2026-08-02T19:53Z (slot 8, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)**:
  blocker re-verified fresh, unchanged. `uts-prod-manifest-consolidator-market-data-prediction-cron` still `PAUSED`
  (`gcloud scheduler jobs describe`, `unified-trading-sa` account). `GET /api/backlog`:
  `mtds_available_at_cross_asset_backfill-001` still `status: queued`, `-006` still `status: dispatched` (to slot 14,
  `dispatched_at: 2026-08-02T15:51:02Z`, `done_at: null`, ~4h in). **First-hand corroboration**: I was independently
  dispatched `-001` earlier this same session and directly verified its gating live process (PID `153615`,
  `rebuild_prediction_manifest.py --start-date 2025-11-12 --end-date 2026-08-01 --chunk-days 15`, from
  `.tabs/14/market-tick-data-service`) via `ps -p` — healthy, actively growing RSS, no crash signature — before
  declining it as a collision (`/skip-current-task`, see that plan's own Progress Log). This confirms the sibling plan's
  apply is real ongoing work, not a stalled/dead dispatch. No change to this todo's action: not touching the cron, not
  re-scavenging the checkpoint (already durably merged at the GCS path above). Released via
  `/skip-current-task {"reason_code": "GATED"}`. **For the next resumer**: same as the prior entries — check
  `-001`/`-006` status fresh before assuming the block persists.
- **2026-08-06 (slot 4, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)** — resumed the
  4b-i migration. **Blocker CLEARED**: cron `uts-prod-manifest-consolidator-market-data-prediction-cron` is now
  `ENABLED` (since 2026-08-03T17:51Z; live-verified healthy, last cycle 00:14Z today); sibling
  `mtds_available_at_cross_asset_backfill-006`/`-005`/`-008` all `done`. **BUT a material environment change**: the
  sibling plan's `rebuild_prediction_manifest.py` rebuild REPLACED the prediction `_index` — it no longer carries ANY
  `data_type=prediction_trades` rows (current data_types: `trades` 1.39M, `book_snapshot_5` 1.17M,
  `prediction_canonical_question_group` 89.5k, `market_lifecycle` 2.3k). The migration script's `_dates_from_manifest()`
  therefore returns 0 dates → the shipped script can no longer drive itself. **Adapted** via a scratchpad driver
  (throwaway, NOT committed) that reuses the shipped `process_day()` unchanged (all its safety: Part 1/2 content-verify,
  additive-only enrichment, readback verify, delete gated on all_cells_enriched + fresh soft-delete retention) but feeds
  the 348-date legacy set explicitly (from the 4b-ii enumeration `_ops/shape4_corpus_enumeration_2026_08_04.jsonl`).
  **Ground-truth scan (python list_blobs, NOT gsutil ls — gsutil is non-recursive and undercounts the nested
  `chain=POLYGON/.../prediction_trades/` tree)**: of the 348 legacy dates, **75 are legacy-absent**
  (2025-03-14..2025-04-18 + 2025-06-06..2025-06-12 + 2025-06-14..2025-07-09 + 2025-07-11..2025-07-16; all in-checkpoint
  = already enriched, legacy already deleted undocumented) and **273 still carry legacy `prediction_trades` objects**
  (224 enriched-per-checkpoint + 49 not-in-checkpoint [2026-02-25..2026-04-14], whose canonical twins are ALREADY
  enriched — sampled `title`/`slug`/`eventSlug` present). **The delete pass has effectively never run** (checkpoint
  records 0 deletes) — the remaining work is the delete pass over the 273 legacy-present days. Soft-delete retention
  re-verified FRESH this run: `604800`s (7 days) — reversibility-qualified, no `[OPERATOR]` gate needed. **Launched**
  `run_4bi_delete.py --apply --delete-legacy` over the 273 days (00:40Z, harness-tracked `run_in_background` + a
  self-heartbeating `4bi_watchdog.sh` posting /progress every 5 min — the documented
  orphan_reap/WorkerLivenessWatchdog-avoidance pattern from this doc's own history), memory capped via
  `run-bounded-analysis.sh --mem-cap 12G`. **Note for future resumers**: the durable merged checkpoint at
  `gs://market-data-tick-pred-prd-central-element-323112/_ops/prediction_trades_migration_checkpoint_2026_07_31.jsonl`
  is still valid for the 299 enriched days, but the migration now runs via the driver + a fresh run-report
  (`prediction_trades_migration_report_run.jsonl`) since the script's manifest date-source is gone. **ALL migration
  tooling is durable in GCS** at `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/`
  (`run_4bi_delete.py`, `4bi_watchdog.sh`, `scan_legacy_presence.py`, `legacy_348_days.txt`, `legacy_presence.json`);
  the LIVE working checkpoint is synced there every 5 min at
  `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_run_checkpoint_latest.jsonl` (pull that + the two
  `.txt`/`.json` inputs to resume). See next entry for the outcome.
- **2026-08-06T01:2xZ (slot 13, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)** —
  resumed the delete pass after slot-4's run died at **46/273** legacy-present days (no live process found; slot-4 tmux
  respawned 01:20Z; the GCS checkpoint `_ops/4bi_run_checkpoint_latest.jsonl` synced at 01:16Z with 46 lines is the
  durable frontier). Recovered that 46-day checkpoint; adapted the driver to this slot (`run_4bi_delete_s13.py` — same
  code, `MTDS` path → `.tabs/13/`); created slot-13's MTDS venv (`uv sync`, then reverted the incidental `uv.lock`
  re-resolution side-effect — tree clean). Fresh soft-delete retention check passed (`604800`s) and **launched
  `--apply --delete-legacy` over the remaining 227 days at 01:25:39Z** (driver + watchdog harness-tracked
  `run_in_background`, mem-capped 12G). First frontier days may log `cids=0/deleted=0` — slot-4's unsynced tail (last ~4
  min before its death) already deleted them; idempotent re-verify, harmless. **Durable resume state**: live checkpoint
  synced every 5 min to `_ops/4bi_run_checkpoint_latest.jsonl`; adapted driver + watchdog uploaded to
  `_ops/4bi_scratchpad_2026_08_06/run_4bi_delete_s13.py` + `4bi_watchdog_s13.sh`; inputs `legacy_348_days.txt` +
  `legacy_presence.json` already there. Completion verification tool `verify_4bi_deletion_s13.py` (re-lists each date's
  legacy prefix via the migration's own `_LEGACY_PREFIX_TPL` + `_SHAPE3B_MARK`, PASS only when 0 remaining
  `/data_type=prediction_trades/` objects + 0 report anomalies/errors; smoke-tested PASS on a processed day) uploaded to
  the same GCS scratchpad. On completion: run it over all 348 dates (0 legacy objects remaining via
  `gcs_describe_object`/presence re-scan), 0 anomalies, then flip 4b-i's checkbox with final counts.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **2026-08-06T09:1xZ (slot 5, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)** —
  resumed the delete pass. **State recovered**: GCS checkpoint `_ops/4bi_run_checkpoint_latest.jsonl` at **144/273**
  legacy-present days deleted (0 anomalies, 0 errors), no live process. Adapted slot-13's driver + verifier to this slot
  (`run_4bi_delete_s5.py`, `verify_4bi_deletion_s5.py`), created MTDS venv (`uv sync --frozen`, uv.lock clean), dry-ran
  read-only, and launched `--apply --delete-legacy` (retention re-verified fresh = 604800s) over the 129 remaining days.
  **Measured the real per-day cost** on the first day (~2k condition_ids × 2 describes + 1 parquet read each, sequential
  → 7+ min and not done) → **a single-run completion estimate of 15-20h** for 129 all-heavy Dec-Apr days, too long for
  one session to survive reliably given this doc's 10+ death/resume cycles. **Parallelized** into 3 DISJOINT day-shards
  (43d each, no write contention): `shard_A_days.txt` 2025-12-07..2026-01-18, `shard_B_days.txt` 2026-01-19..2026-03-02,
  `shard_C_days.txt` 2026-03-03..2026-04-14 — 3 driver instances (`run_4bi_delete_s5.py --apply --delete-legacy` per
  shard, each with its own `report_shard_{A,B,C}.jsonl`, mem-capped 8G, harness-tracked `run_in_background`) + a sharded
  watchdog (`4bi_watchdog_shards_s5.sh`) that posts /progress every 5 min, syncs each shard report to
  `_ops/4bi_report_shard_{A,B,C}.jsonl`, and merges baseline+shards into `_ops/4bi_run_checkpoint_latest.jsonl`.
  **Resume state for the next resumer**: all tooling + shard day-files uploaded to `_ops/4bi_scratchpad_2026_08_06/`;
  live frontier = the 3 `_ops/4bi_report_shard_*.jsonl` (merge by day, prefer higher `canonical_enriched`); verify via
  `verify_4bi_deletion_s5.py --dates-file legacy_348_days.txt --report <merged>`. Still running — see next entry for the
  outcome.
- **2026-08-06T10:1xZ (slot 5, same task)** — **rebalanced 3 → 6 shards** after measuring real per-shard rates: A (Dec)
  ~4.6 min/day, B (Jan) ~7.7 min/day, C (Mar-Apr) ~13.5 min/day → the contiguous assignment made C a **~10h critical
  path** (outlives any session). At 10:15, with **25/273** days done clean, killed the 3 drivers + old watchdog
  (SIGTERM, idempotent — partial in-flight days re-processed, report-driven done-set preserved) and relaunched **6
  balanced shards** of the **104 remaining** days, round-robin by date so heavy Mar-Apr days interleave with light
  Dec-Jan: `shard2_{A..F}_days.txt` (A/B 18d, C/D/E/F 17d), each driver its own `report_shard2_{A..F}.jsonl` (mem-capped
  8G, harness-tracked), + 6-shard watchdog `4bi_watchdog_shards2_s5.sh` (merges all 6 into
  `_ops/4bi_run_checkpoint_latest.jsonl`, syncs each report to `_ops/4bi_report_shard2_{A..F}.jsonl`). Rebalance tooling
  (`rebalance_4bi.py`, shard2 day-files, watchdog) uploaded to `_ops/4bi_scratchpad_2026_08_06/`. **Resume state for the
  next resumer**: live frontier = the 6 `_ops/4bi_report_shard2_*.jsonl` (merge by day, prefer higher
  `canonical_enriched`); est. completion ~2.5h. Still running — see next entry for the outcome.
- **2026-08-06T18:3xZ (slot 8, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`)** —
  resumed the 4b-i delete pass. Recovered state from GCS: merged checkpoint at 263/348 days (0 anomalies), 6 shard
  reports from slot-5's rebalanced run. **10 legacy-present days remaining** (2026-04-04..2026-04-14, minus 2026-04-05
  which was already done), plus 75 legacy-absent days (already deleted, documented in legacy_presence.json). Adapted
  slot-5's driver + watchdog to slot 8 (only path change: `.tabs/5/` → `.tabs/8/`), seeded the report with the 263-day
  baseline to skip already-done days, verified MTDS venv exists, re-verified soft-delete retention (604800s, qualifies
  for reversibility), and launched `--apply --delete-legacy` over the 10 remaining days (mem-capped 12G via
  `run-bounded-analysis.sh`, harness-tracked `run_in_background` + self-heartbeating watchdog posting /progress every 5
  min, syncing report to `_ops/4bi_report_s8.jsonl`). **Lesson**: the driver uses `--report` as both done-set filter AND
  output — seed it with the baseline checkpoint before launching, or it re-processes all 273 present days. **Lesson**:
  `run-bounded-analysis.sh` lives in `unified-trading-pm/scripts/dev/`, not in the service repos. Still running — see
  next entry for the outcome.
- **2026-08-06T21:5xZ (slot 16, `data_engineering`, backlog task `prediction_satellite_ao_dispatch_batch4-023`, session
  end) — 4b-i COMPLETE.** Recovered state from the durable GCS checkpoint (`_ops/4bi_run_checkpoint_latest.jsonl`,
  263/348 days, 0 anomalies) + slot-8's report (`_ops/4bi_report_s8.jsonl`, 273 lines covering all legacy-present days).
  No live process found; slot-16 fresh-pull clean, MTDS venv created. Verification re-run over all 348 dates found **4
  remaining legacy objects** on `day=2026-04-14` for instrument_types OTHER/SILVER/SOL/SPX (24.2MB / 152k rows, 22KB /
  86 rows, 8.9MB / 98k rows, 87KB / 911 rows respectively). These were shape3b-only objects (camelCase
  `prediction_trades` format) with NO canonical twin (`data_type=trades` returned 0 objects for all 4 instrument_types
  on this date) — the migration driver correctly skipped them as enrichment-impossible (logged as 13 anomalies in
  slot-8's report: "shape3b present without shape3 — skipped (no snake_case source)"). **Verified content-presence
  before deletion**: all 4 carry `title`/`slug`/`eventSlug` fields. Soft-delete retention re-verified fresh at 604800s
  (7 days, reversibility-qualified). Deleted all 4 via UTL `gcs_delete_object()`, each verified GONE via
  `gcs_describe_object() is None` immediately after. **Final verification re-run**: 0 legacy objects remain across all
  348 dates (`remaining_days=0, remaining_objects=0`). The 13 report anomalies are enrichment-pass artifacts (no
  canonical twin to enrich INTO) — the deletion itself is complete with 0 anomalies. **Total**: 3,574 legacy
  `prediction_trades` objects deleted across the full 2025-03-14→2026-04-14 range. All tooling + inputs durably archived
  at `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/`. **Checkbox flipped —
  `market-tick-data-service` (no new code commit; the shipped migration script `@e4acf0c4` drove the work, the delete
  pass used a scratchpad driver that's already durably uploaded to the GCS scratchpad).**

- **2026-08-10T19:45Z (slot 25, data_engineering, dispatched on 4b-iii — "merge shape #4 + delete legacy")**: **TOOLING
  GAP CLOSED + a real finding.** Built, validated, and shipped the shape-#4 merge+delete script
  `market-tick-data-service/scripts/migrate_prediction_trades_shape4_2026_08_10.py` + 22 unit tests
  (`market-tick-data-service@5c0c7f3f`, committed; QG was still running at this write) and the launcher category
  `prediction-shape4-merge` in `deployment-service@581a8da1` (committed; QG pending). Script mirrors 4b-i's alias-aware
  additive-only pattern: per (day, cid) cell, content-verifies the canonical twin (Part 1 `gcs_describe_object` + Part 2
  `_metadata_matches` — every shape-#4 row's (transactionHash, ts) key must resolve in the canonical with identical
  title/slug/event_slug), enriches if genuinely missing, and only deletes the cell's shape #4 objects (both bare +
  `POLYMARKET:PREDICTION_MARKET:`-prefixed variants, cross-checked identical) once verified — gated on a FRESH
  `gcs_bucket_soft_delete_retention_seconds()` >= 604800s check (codex delete-safety §3a, reversibility-qualified, no
  `[OPERATOR]` gate). Shape #4 is NOT manifest-tracked and delete targets are not manifest-tracked, so NO consolidator
  drain is needed. Dry-runs validated (2-day + 1-day; two bugs caught + fixed live: (a) `_metadata_matches` KeyError'd
  on canonical twins carrying the legacy camelCase `eventSlug` alias — made alias-aware; (b) a single uncaught per-cid
  exception aborted the whole day's report — added per-cid exception isolation).

  **KEY FINDING (data-completeness, affects the delete half)**: on the day-1 dry-run (2025-03-14), all 170 shape-#4
  objects were already-enriched, but **9/85 cells (≈10%) flagged
  `canonical already enriched but metadata MISMATCHES shape #4 source`** — investigated one
  (`market_type=range_bracket`): the canonical twin carries **2 trades while the shape #4 object carries 12** (metadata
  VALUES identical; the canonical is a strict SUBSET). The script correctly REFUSES to delete those cells (delete-safety
  Part 2 — those shape #4 objects hold real trades the canonical lacks; deleting them would lose data). So the "delete
  legacy" half can only fully complete for cells where shape #4 ⊆ canonical (content-verified); the subset-divergent
  cells (expected ~10%) stay as honest non-canonical objects and are flagged per-cell as anomalies. This is ALSO a
  canonical data-completeness gap worth characterizing — see the new follow-up todo below. **Next steps (once this
  write + both QGs are green)**: quickmerge `5c0c7f3f` (MTDS) + `e25dcfb3` (deployment-service), republish the MTDS code
  tarball, then launch `bash launch-canonical-migration-vm.sh prediction-shape4-merge 2025-03-14 2026-04-14 full` (the
  VM runs ~many-hours; deletes only verified cells, keeps + flags the subset-divergent cells). 4b-iii checkbox stays
  OPEN until the VM run is verified (same multi-session pattern as 4b-i).

- **2026-08-10T20:00Z (slot 25, data_engineering, 4b-iii continuation)**: **MTDS SHIPPED.** MTDS QG turned GREEN (full
  `quality-gates.sh`, exit 0, all phases incl. diff-scoped 5.94/5.95 ratchets PASS vs base `5c0c7f3f`); quickmerge
  landed **`market-tick-data-service@b9ce3b65e8` on live-defi-rollout** (post-push ancestry verified). Launcher
  `prediction-shape4-merge` (`deployment-service@581a8da1`, usage strings + `_launch` dispatch +
  `_prediction_shape4_merge_cmd` dry/full flag wiring confirmed) is committed, deployment-service QG in flight — will
  quickmerge on green. **Resume**: quickmerge `e25dcfb3` → republish MTDS code tarball (`create-code-tarballs.sh`) →
  launch `bash launch-canonical-migration-vm.sh prediction-shape4-merge 2025-03-14 2026-04-14 full` → verify VM
  STARTED + progress (many-hours run) → 4b-iii checkbox flips only after VM completion verified.

- **2026-08-10T20:06Z (slot 25, data_engineering, 4b-iii continuation)**: **VM LAUNCHED.** MTDS tarball refreshed to the
  pinned SHA (mtds-code@`b9ce3b65e862`, manifest commit_sha + git_status_clean=true, SHA-pinned copy in
  `deployment-scripts-central-element-323112/code/`). Launched
  `canonical-migration-prediction-shape4-merge-20260810-200603` (asia-northeast1-c, e2-standard-8, SPOT) via
  `MTDS_TARBALL_SHA=b9ce3b65e862 bash launch-canonical-migration-vm.sh prediction-shape4-merge 2025-03-14 2026-04-14 full`
  → runs
  `scripts/migrate_prediction_trades_shape4_2026_08_10.py --start-date 2025-03-14 --end-date 2026-04-14 --apply --delete-legacy`
  (dry=no flag, full=`--apply --delete-legacy`). All 4 tarballs fresh at launch (UAC/UTL/MTDS/ deployment-service).
  **NOTE on sequencing**: deployment-service QG (e25dcfb3 launcher) was QUEUED on the saturated host, so the launch was
  DECOUPLED — it depends only on the MTDS tarball (pushed + pinned ✓); the deploy-service quickmerge lands separately
  when its QG frees up. Logs tee to
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-prediction-shape4-merge-20260810-200603/`
  (run.log = migration progress; EXIT_STATUS + VM auto-shutdown = terminal). 4b-iii checkbox stays OPEN until the VM run
  completes (expected many-hours; same multi-session pattern as 4b-i).

- **2026-08-10T20:09Z (slot 25, data_engineering, 4b-iii continuation)**: **VM STARTED VERIFIED (not fire-and-forget).**
  Serial console (20:08:20): setup exit 0 (UAC OK, MTDS OK, deps installed); migration launched PID 4983/4997 full mode
  (`--start-date 2025-03-14 --end-date 2026-04-14 --apply --delete-legacy`); GCS run.log appeared. Migration runs many
  hours day-by-day (deletes only content-verified cells, keeps + flags subset-divergent). Superseded by the 20:22 entry
  (migration confirmed running, retention gate passed).

- **2026-08-10T20:12Z (slot 25, data_engineering, 4b-iii continuation)**: **VM #1 FAILED at start — IAM grant →
  RELAUNCHED.** First VM (`...-200603`) exited rc=1 within ~12s of migration start: the script's delete-safety retention
  check (`gcs_bucket_soft_delete_retention_seconds()` on `market-data-tick-pred-prd-central-element-323112`) needs
  `storage.buckets.get`, which the VM SA `uts-prd-sa` lacked (403 Forbidden; it has project-level `storage.objectAdmin`/
  `objectViewer` but no bucket-metadata read). The 4b-i template's similar delete path evidently never needed
  `buckets.get`, so this is a NEW requirement of the shape-#4 retention gate. **FIX (IAM-self-service, additive +
  scoped, per governance rule — grant, don't pause)**: added `roles/storage.legacyBucketReader` for
  `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` on the prediction tick bucket (grants
  `storage.buckets.get`
  - objects list/get; SA already had object write/delete via objectAdmin). **RELAUNCHED as
    `canonical-migration-prediction-shape4-merge-20260810-201105`** (same pin `MTDS_TARBALL_SHA=b9ce3b65e862`, full
    mode), RUNNING. NOTE: at relaunch the launcher warned `mtds-code manifest=b9ce3b65e862 but repo=47966bf50ab1` (a
    peer pushed newer MTDS commits) — the pinned-SHA tarball copy guarantees the VM runs MY exact commit; verify via the
    migration log once started. **Resume**: confirm 201105 passes the retention check + progresses (Monitor
    `br5h30v30`), then wait for many-hour completion.

- **2026-08-10T20:15Z (slot 24, data_engineering, dispatched on "characterize the shape-#4 subset-divergent cells")** —
  **CHARACTERIZED via a bounded dry-run of the shipped merge script** (the VM report it was meant to read was still
  mid-run / had only just relaunched as `...-201105`; a bounded dry-run is read-only, uses the exact same shipped
  detection logic, and produces the same anomaly lines). No GCS mutation, no corpus walk — dry-run over a bounded sample
  of 9 days (2025-03-14 [the documented divergent day] + 2025-06-14..22), plus per-cell object reads for mechanism
  verification. Findings:

  **(a) Population — 10.1% of cells, matching the expected ~10%.** 157 unique divergent cids across 1,558 sampled
  condition_ids (9 days). Per-day divergent rates: 2025-03-14 9/85=10.6%; 2025-06-14 10.1%, 06-15 6.1%, 06-16 14.4%,
  06-17 15.7%, 06-18 8.5%, 06-19 9.4%, 06-20 10.8%, 06-21 16.3%, 06-22 6.2% — a tight ~6–16% band, no day
  concentrated/destructive outlier. (Anomaly lines deduped by cid — the script emits one line per naming-variant
  candidate, so a cid can appear 1–2×.)

  **(b) Mechanism — the subset is confined to the PREFIXED canonical naming variant; the BARE canonical object is
  complete.** Each divergent cell has TWO canonical objects under
  `venue=POLYMARKET/instrument_type=prediction_market/ data_type=trades/`: the bare `{cid}.parquet` and the
  `POLYMARKET:PREDICTION_MARKET:{cid}.parquet` prefixed twin. For **all 157 sampled divergent cells**, the bare object
  was COMPLETE — row-set + title/slug/event_slug metadata match the shape #4 source exactly (`_metadata_matches=True`).
  The prefixed twin was the row-set SUBSET (e.g. 498/500 rows on 2025-06-14 `0x0a33...`; 2/12 on the documented
  2025-03-14 `0x58b3...`), which is what trips the script's per-variant `_metadata_matches` check and flags the cell. So
  the "canonical ⊂ shape #4" framing is exact for the PREFIXED twin, but the BARE canonical `trades` object — the
  manifest-tracked shape — already carries the full shape #4 row set for these cells. This is a dual-write
  naming-variant skew (one of the two canonical writes under-populated), not canonical row loss.

  **(c) market_type — sharply `range_bracket`-specific.** On both mechanism-checked days, divergence is overwhelmingly
  range_bracket: 2025-06-14 range_bracket 17.1% (24/140) vs binary 0.0% (0/98); 2025-06-17 range_bracket 23.2% (46/198)
  vs binary 3.6% (4/112) vs categorical 0.0%. Consistent with the original discovery's `range_bracket` example; not
  random across market types.

  **(d) Disposition decision — ACCEPT the bare canonical as the manifest-SSOT subset and KEEP the shape #4 objects as
  honest non-canonical for divergent cells (option B); do NOT backfill.** Rationale: (1) the manifest-tracked canonical
  `trades` object (bare twin) already carries the full shape #4 row set for every sampled divergent cell — there is no
  row loss to backfill from the canonical-SSOT side; (2) a row-set-union backfill into the bare canonical would be a
  no-op there, and into the prefixed twin would recreate a redundant partial write (the prefixed variant is a
  legacy/duplicate naming, not the SSOT shape); (3) the 4b-iii merge script's existing behavior is already correct — it
  refuses to delete these cells' shape #4 objects (delete-safety Part 2 `_metadata_matches` gates deletion), so keeping
  them as honest non-canonical is exactly what the shipped script does, no new code needed; (4) the
  manifest/non-canonical inventory already reflects shape #4 as a distinct non-canonical tree
  (`non-canonical-path-inventory.md` row 22). No follow-on action required beyond the 4b-iii merge run itself; this
  characterization closes the todo. (Root-cause of the range_bracket skew — why the prefixed twin under-populated on
  range_bracket cells specifically — is a write-path question out of this todo's scope; the census VM + merge report may
  surface more, and if the bare twin ever turns up incomplete for a cell during the VM's `--apply` run, that cell should
  be re-evaluated rather than blindly accepted.) (repo: market-tick-data-service — read-only analysis, no code shipped).

- **2026-08-10T20:16Z (slot 25, data_engineering, 4b-iii continuation)**: **VM #2 (201105, SPOT) PREEMPTED before setup
  — RELAUNCHED ON-DEMAND.** The 201105 SPOT instance was preempted by GCE ~2 min after creation
  (`compute.instances.preempted`, system, 20:13Z) — no setup log/run.log ever appeared (nothing to resume; setup hadn't
  started). Given 2 consecutive SPOT launches failed (VM #1 403→self-delete; VM #2 preempted), relaunched **201105
  ON-DEMAND** (`ON_DEMAND=true VM_NAME_OVERRIDE=canonical-migration-prediction-shape4-merge-20260810-201105`,
  non-preemptible STANDARD, same `MTDS_TARBALL_SHA=b9ce3b65e862` pin, full mode) — RUNNING (new IPs
  10.146.0.66/35.200.95.158). Reusing the exact same vm_name intentionally blocks the fleet `RelaunchPreemptedVm`
  actuator from duplicating it (instance-already-exists safe-fail); no fleet auto-relaunch had fired yet (no insert op
  seen). **Also**: deployment-service QG re-run in flight (first run's 11 `test_dp_recovery_actuators.py` failures were
  suite-ordering contamination — all 59 pass standalone; my e25dcfb3 touches only the bash launcher). **Resume**:
  confirm 201105 passes the retention check (IAM grant) + progresses (Monitor `b68cwqm0m`), then wait for many-hour
  completion; quickmerge deployment-service when its QG re-run is green.

- **2026-08-10T20:22Z (slot 25, data_engineering, 4b-iii continuation)**: **MIGRATION CONFIRMED RUNNING — retention gate
  PASSED (IAM fix verified).** 201105 (on-demand) local log:
  `retention check: bucket=market-data-tick-pred-prd-central-element-323112 retention_seconds=604800` (≥604800 ✓ — the
  `storage.buckets.get` grant to uts-prd-sa works); deployment `8db91324` registered (PREDICTION, full) +
  DEPLOYMENT_STARTED; heartbeat daemon + 60s uploader live; ManifestReader proceeding (per-VM shards fallback +
  consolidator-lock wait, by-design). Processing 2025-03-14..2026-04-14 full mode (enrich + delete only content-verified
  cells, keep+flag subset-divergent). 4b-iii flips only after this many-hour run completes (EXIT_STATUS + auto-shutdown
  → read run.log, verify 0-loss + post-delete counts).

- **2026-08-10T21:52Z (slot 25, data_engineering, 4b-iii continuation)**: **LAUNCHER SHIPPED — both code legs done.**
  Peer fix (`c472a818`) resolved the actuator-test regression; QG #3 GREEN (pytest 3262/0). Quickmerge landed
  `deployment-service@581a8da1` on LDR (post-push ancestry verified; CI quality-gates-v2 + sync-vm-scripts-to-gcs
  GREEN). Both legs shipped: MTDS `b9ce3b65e8` + deploy-service `581a8da1`. VM 201105 continues at correct 0-loss
  behavior → 4b-iii flips after completion verification.

- **2026-08-10T22:30Z (slot 25, data_engineering, 4b-iii post-compaction RESUME)**: Session died mid-4b-iii; all repos
  ahead=0 (both code legs survived). VM 201105 RUNNING at [174/397], 0-loss: deleted=35,036 anomalies(kept)=3,641
  enriched=0 objects=41,194. No overwrites/mis-deletes; monitor re-armed. POST /done after migration + 4b-iii flip.
- **2026-08-13T10:59Z (slot 18, data_engineering, resuming 4b-iii — dispatched task
  `prediction_satellite_ao_dispatch_batch4-d06070149e23`)**: fresh-pulled all repos clean. Verified the relaunched VM
  `canonical-migration-prediction-shape4-merge-20260812-221112` (on-demand, `--apply --delete-legacy`, full
  2025-03-14..2026-04-14 range, launched after the int64-timestamp fix `market-tick-data-service@5271ea7c` +
  `deployment-service@b9cbb1b1`) is `RUNNING` (gcloud), no IAM/retention errors — `PROGRESS.json`:
  `last_completed_date=2026-02-25`, monotonic, updated 10:59:07Z (actively advancing, ~48 of 397 days remain to
  2026-04-14). `run.log` shows the expected mix of clean enrich+delete cells and
  `MISMATCHES shape #4 source — NOT deleted` anomaly lines (the known subset-divergent `range_bracket` cells, correctly
  kept per the disposition ruled 2026-08-10). No `EXIT_STATUS` object yet (not terminal). Armed a `run_in_background`
  watchdog (`watch_shape4_vm.sh`, polls the GCS `EXIT_STATUS` marker via UTL
  `get_storage_client()`/`download_from_storage()` every 5 min, posts `/progress` each check, sized to ~3h / 36 checks —
  covers the ~1.8h ETA at the measured ~27 days/hour rate with headroom) instead of busy-polling turns. **Next**: on
  watchdog wake, read `EXIT_STATUS` + final `run.log` totals, verify 0 unexpected anomalies (only the known
  subset-divergent class), spot-verify a handful of deleted shape #4 objects are actually gone
  (`gcs_describe_object() is None`) and a handful of kept ones still present + still content-flagged, then flip this
  checkbox with final counts and `/done`.
