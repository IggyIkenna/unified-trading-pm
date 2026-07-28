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

- **[CODE] P1. Extend the canonical `trades` schema for POLYMARKET metadata + migrate the legacy `prediction_trades`
  population** — ROLLUP (split 2026-07-28, slot-12, into 4a DONE + 4b open; see below). Operator ruling 2026-07-25
  (`unified-trading-pm@7dfcfe0ee`,
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
  - [ ] [DATA] P1. **4b-i — migrate shapes #3/#3b (session-doable slice; IN PROGRESS 2026-07-28, slot-16).** Enrich the
        existing canonical `data_type=trades` objects with `title`/`slug`/`event_slug` recovered from the legacy
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
  - [ ] [SCRIPT] P2. **4b-ii — shape #4's corpus-wide extent (Tier-2 SPOT-VM single walk, separately dispatched).**
        Shape #4 (10-segment `data_source=POLYMARKET_CLOB/...` tree) is explicitly OUT OF SCOPE for 4b-i — its
        corpus-wide extent is GENUINELY UNKNOWN (the issue doc's "158+" figure is a ONE-DAY `day=2025-04-11` sample
        only, live-confirmed exactly 158 objects for that one day, not a corpus total). Enumerating every day shape #4
        exists on IS a new whole-corpus walk (review-blocking per CLAUDE.md single-walk discipline) — it must run as the
        ONE sanctioned Tier-2 SPOT VM single walk per `/codex/02-data/reconciliation-census-and-compute-tiers.md`.
        **Re-tagged off `[OPERATOR]` (2026-07-28)**: the safe-idempotent justification per CLAUDE.md's VM-launch-gating
        OR-clause is stated directly — this walk is a READ-ONLY enumeration (no GCS mutation), cheaply re-run on
        preemption (idempotent re-listing, no partial-state risk), so it launches via the standard Tier-2 SPOT VM
        single-walk mechanism without a separate operator sign-off. Once the corpus-wide extent is known, the merge
        logic is the SAME read-transform-write-per-cell pattern as 4b-i's shipped script (shape #4 already carries
        `title`/`slug`/ `eventSlug` per the issue doc's content-verify — the merge direction may in fact be shape#4 ->
        shape#1, richer source into the (possibly still-bare) canonical twin, mirroring 4b-i's alias-aware additive-only
        approach). Repo: market-tick-data-service. **Done when**: shape #4's full corpus-wide object set is enumerated
        (VM-run), merged into canonical with a verified 0-loss content-check per delete-safety Part 2, and legacy
        objects deleted only after verification.
  - [ ] [DATA] P2. **4c — register the writer cutover in `canonical-cutover-register.md` +
        `non-canonical-path-inventory.md`.** 4a's writer-root fix (title/slug/event_slug now flow to new canonical
        writes) is registerable now; the raw-object migration disposition (4b-i shapes #3/#3b, 4b-ii shape #4) must be
        added/updated once each actually executes — don't mark the `prediction_trades`/shape-#4 rows
        `yes-twin-confirmed` until they are. Repo: unified-trading-pm.

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
  (P2/P3 residual-manifest items, both "NICE-TO-HAVE", both "ride the next prediction canonicalisation walk").
- **[SCRIPT] Re-enumerate the IS POLYMARKET universe for a recent past date → re-run the `book_snapshot_5` batch
  backfill → verify `row_count>0`.** A bounded, idempotent re-enumeration+backfill; it shares the POLYMARKET IS
  enumeration path with todo #1 so it should sequence AFTER #1 lands (else it re-enumerates against the old write path).
  **Re-tagged off `[OPERATOR]` (2026-07-28)**: the safe-idempotent justification already stated here (the shard re-runs
  cleanly on preemption) satisfies CLAUDE.md's VM-launch-gating OR-clause — launches via the standard backfill-VM
  mechanism, no separate operator sign-off needed. Source: `prediction_live_clob_depth_capture_2026_07_24.md` (the
  "DEFERRED-CROSS-DEP" `book_snapshot_5` row-proof item).

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
- 2026-07-28 (slot-16, data_engineering): split 4b into 4b-i (shapes #3/#3b, session-doable) + 4b-ii (shape #4,
  operator/VM-gated) per the todo's own "next steps". Built + shipped `market-tick-data-service@e4acf0c4`
  (`scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py`, 20 unit tests, QG green) after live-verifying the
  actual GCS schema/paths (manifest read: 2,477 rows/348 dates confirmed; sampled 6 dates across the full range
  confirmed the canonical shape#1 twin exists everywhere, correcting an initial worry that it might be
  date-range-gated). Caught + fixed a real join-key-typing bug (int vs str) and a real overwrite risk (some canonical
  objects already carry a richer pre-existing schema with title/slug under different column names) via the script's own
  dry-run safety checks before any prod write. Launched the real `--apply` enrichment run across all 348 dates
  (resumable, additive-only, 0 anomalies through the first ~50 dates at last check) — running in background; the delete
  pass (`--delete-legacy`, gated on a live-verified `604800`s soft-delete retention on the prediction bucket) follows
  once enrichment completes and a sample is spot-verified. 4b-i's checkbox stays open until the full 348-date run +
  delete pass verify complete.
- 2026-07-28 (slot-16, session end): the `--apply` run above got to **55/348 dates (0 anomalies)** before this worker
  session died mid-run — a background-process reap (exit 144/SIGTERM), NOT a script defect; every write up to that point
  content-verified before commit and is durable in GCS already. **Lesson**: a plain `nohup ... & disown` inside a single
  Bash tool call does NOT survive a harness session death the way `run_in_background: true` does — use the latter for
  any long-running mutating job you need to survive a session boundary. **Remaining work (next session/worker)**: (1)
  resume the enrichment — re-run
  `.venv/bin/python scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py --apply --report <path>` from
  `market-tick-data-service` (idempotent even without the report file — `all_fields_present` skips already-enriched
  cells on read); (2) once all 348 dates enrich clean, run `--delete-legacy` (re-verify the soft-delete retention fresh,
  don't assume the `604800`s measured here still holds); (3) flip 4b-i's checkbox with the final counts; (4) do 4c's
  registration once (1)+(2) land.
- 2026-07-28 (slot 7, resuming from slot-16's 55/348 hand-off): resumed via
  `.venv/bin/python scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py --apply --report <scratchpad>/prediction_trades_migration_report.jsonl`
  (exported `GCP_PROJECT_ID`/`CLOUD_PROVIDER` first — not pre-set in this session). **Hit slot-16's exact "session died
  mid-run" bug a second time**, this time root-caused precisely (not just "not a script bug"): backgrounded with
  `nohup ... & echo $!` inside a plain Bash call, detaching it from the tracked session tree —
  `agent-orchestrator/server/orphan_reap.py`'s periodic sweep classified it as an orphan and SIGKILLed it ~346s later
  (`journalctl -k`: `orphan_reap sweep: slot 7 pid 4006112 age=346s KILLED`). Already-known, already-filed
  (`plans/active/issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`, filed 2026-07-27, its
  own recommended fix left unshipped) — shipped it now: `unified-trading-pm@38e6de9fa` adds a `nohup`-avoidance callout
  to `agents/worker.md`'s Heartbeat section + fresh evidence in the issue doc. Resumed correctly the second time (long
  command passed directly to `run_in_background: true`, no `nohup`) — ran clean for ~25 min, then hit a SECOND,
  DIFFERENT kill: `WorkerLivenessWatchdog` read this slot as heartbeat-stale (no `/progress` call in >25 min while doing
  local-only bash progress checks) and fired `kill_session(orch-slot-7)`, which SIGTERMs the whole pane's descendant
  tree by design (`_reap_pane_tree`) — collateral-killing the properly-parented backfill despite it being immune to
  `orphan_reap`. Root-caused via `journalctl | grep kill_session` (a different log signature from `orphan_reap sweep`),
  documented as `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` § "Watcher coverage" item 5 + a
  cross-reference addendum in the nohup issue doc — **`run_in_background` fixes orphan-reap, it does NOT exempt a worker
  from the `/progress` heartbeat cadence while monitoring a long job.** Resumed a third time with disciplined
  `/progress` heartbeats every ≤8 min going forward. **Status at last check**: 67/348 dates done, 0 anomalies, real
  enrichment writes now dominant (past the range slot-16's manual pass + the 4a writer-root fix's retroactive coverage
  already covered). Still running — see this task's next Progress Log entry for the outcome.
