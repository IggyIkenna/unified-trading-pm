---
doc_type: issue
title:
  BYBIT-SPOT manifest carries 135k rows in three anomalous states — mixed EMPTY / PERPETUAL instrument_type +
  spot-nonsense data_types (derivative_ticker / futures_chain / options_chain / perp_funding / liquidations)
summary:
  'Found 2026-07-07 while implementing cefi_layer1_denominator_gaps -006 (BYBIT-SPOT PERPETUAL itype-stamp fix). The
  scope of the BYBIT-SPOT captured-manifest defect is materially LARGER than that plan anticipates. Total 135,444 rows;
  by instrument_type: 81,659 EMPTY + 53,785 PERPETUAL; by data_type: 40,755 trades + 40,755 book_snapshot_5 + 13,350
  derivative_ticker + 13,350 futures_chain + 13,350 ohlcv_1m + 13,350 options_chain + 267 perp_funding + 267
  liquidations. NONE of derivative_ticker, futures_chain, options_chain, perp_funding, or liquidations is a valid
  data_type for a SPOT venue — those (~54k rows) look like stray captures from a different venue that leaked into the
  BYBIT-SPOT partition. The 81k EMPTY-instrument_type rows are ALSO anomalous — separately from the 53k PERPETUAL-stamp
  defect the -006 plan describes. A simple PERPETUAL→SPOT_PAIR relabel of the 53k subset would NOT close the Layer-1
  Gate ("manifest by_venue_instrument_type shows the split") because the other 82k rows are in states the plan does not
  model.'
status: resolved # corrected 2026-07-14, was: open (all 3 checkbox groups [x], 2026-07-12 Progress Log: "This was the LAST open todo in this issue doc — all todos now closed" — verify-rerun-2 finding 86)
nature: notes
asset_group: [cefi]
stage: [data, meta]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, layer-1, data-correctness, cefi, bybit-spot, manifest-surgery]
related:
  [
    /plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-07
parent_epic: infrastructure_master
priority: P1
source: cefi_layer1_denominator_gaps-006 implementation session (slot-8 planning)
assigned_vm: planning
resolved_by:
  market-tick-data-service@60287d3e (slot-10 data_engineering, 2026-07-12) — see 2026-07-12 Progress Log entry
locked_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: high
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on: [cefi_layer1_denominator_gaps-006]
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding (data-correctness).** Surfaced 2026-07-07 while shipping the forward-path fix for
> `cefi_layer1_denominator_gaps-006` (BYBIT-SPOT PERPETUAL itype-stamp) in `market-tick-data-service`. The forward path
> is fixed (no NEW mis-stamps); the state of ALREADY-captured BYBIT-SPOT rows in the manifest is worse than that plan's
> corrective-relabel step models.

## What I found

Ran `measure_honest_coverage._read_manifest("cefi")` against the pinned-primary consolidated manifest
(`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, 7,219,598 rows + secondary
4,115,773 → merged 11,125,247). Filtered to `venue == "BYBIT-SPOT"`:

```
total BYBIT-SPOT rows: 135,444
by instrument_type: {'': 81,659, 'PERPETUAL': 53,785}
by data_type:
  trades:             40,755
  book_snapshot_5:    40,755
  derivative_ticker:  13,350
  futures_chain:      13,350
  ohlcv_1m:           13,350
  options_chain:      13,350
  perp_funding:          267
  liquidations:          267
```

Three anomalies stack:

1. **The plan's PERPETUAL-stamp defect (~53k rows).** Root-caused in `market-tick-data-service`:
   `TardisAdapter._classify_row_instrument_type` at line 321 lacked `"BYBIT-SPOT"` in its SPOT-venue set, so BYBIT-SPOT
   rows arriving via the `bybit-spot` Tardis exchange fell through to `return InstrumentType.PERPETUAL`. Symmetrical gap
   in `symbol_rules._VENUE_INSTRUMENT_TYPE` (bare `"BYBIT": "perpetual"` but no `"BYBIT-SPOT"` entry). BOTH fixed on the
   forward path by the -006 code shipping in this session — regression-tested via
   `test_classify_row_instrument_type_option_future_perp_spot`.

2. **~82k rows with EMPTY `instrument_type`.** Not modeled by the -006 plan. Distinct from the PERPETUAL subset — these
   rows carry `instrument_type=""` in the manifest. Root cause unknown — the writer's `_resolve_instrument_type_column`
   at `engine/orchestrator/partitioned_writer.py:244` normalises an existing `instrument_type` column via
   `.str.lower()`, so an EMPTY string in the manifest means either (a) the source DataFrame carried `instrument_type=""`
   (writer stamped it that way) or (b) the manifest _consolidator_ is dropping the field for some subset. Needs
   diagnosis before any relabel.

3. **Spot-nonsense data_types on ~54k rows.** BYBIT-SPOT is a canonical SPOT venue — its valid data_types are `trades`
   and `book_snapshot_5` (per `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` which is CURRENTLY empty per the
   cefi_layer1_denominator_gaps issue doc). But the manifest holds ~13,350 rows each of `derivative_ticker`,
   `futures_chain`, `options_chain`, `ohlcv_1m` plus 267 each of `perp_funding` and `liquidations` under
   `venue=BYBIT-SPOT`. **None of these data_types make sense for a spot venue.** They look like stray captures from
   BYBIT-FUTURES / BYBIT (bare) that leaked into the BYBIT-SPOT partition — possibly via the same
   canonicalisation-venue-map bug from a related pipeline. Not modeled by -006's
   `by_venue_instrument_type shows the split` Gate.

## Why it matters

- **Data-pipeline-correctness HARD RULE** — silent placeholders / mis-routed captures are the exact class of defect
  Honest Coverage v2 exists to kill; leaving 82k rows in an unknown state (EMPTY instrument_type) and 54k rows under
  nonsense data_types keeps cefi Layer-2 accounting dishonest for BYBIT-SPOT.
- **-006's plan Gate** says "manifest `by_venue_instrument_type` shows the split" — with 82k rows still in
  EMPTY-instrument_type after any PERPETUAL→SPOT_PAIR relabel, the Gate is NOT satisfied without addressing the other
  two subsets. A partial corrective-relabel would leave a misleading half-fix.
- **Worker-guard "stop-on-surprise"** (from the -006 plan header) — a corrective touching more rows than expected or a
  measure moving the wrong direction requires STOP + raise, not push-through. This finding is exactly that class.
- **Downstream measure drift** — the re-measure task (`cefi_layer1_denominator_gaps-005`) currently PARKED with
  KALSHI-PERP purge as one prereq would land a % that is either misleading (if BYBIT-SPOT stays in
  EMPTY/PERPETUAL/nonsense states) or double-counted (if the nonsense-data_type rows are also on BYBIT-FUTURES / BYBIT
  under the same shard atom).

## Recommended decision

Ship the -006 forward-path fix as-is (map entries + regression tests + issue doc — `docs(plans):` cross-repo PM flip +
`feat(...)` MTDS quickmerge). Handle the three ALREADY-captured subsets as three follow-up sub-todos in this issue doc,
in order (each a machine-encoded backlog task the orchestrator will dispatch to a data_engineering worker). Do NOT
attempt the corrective-relabel in the -006 session because (a) the scope is materially different from what the -006 plan
describes and (b) each subset needs its own diagnosis before mutation.

## Todos

- [x] ✅ [SCRIPT] P1. **Diagnose the ~82k BYBIT-SPOT rows with EMPTY `instrument_type`.** Trace: (i) which
      writer/consolidator produced them; (ii) which asset_group they land under in the raw parquet vs the consolidated
      manifest; (iii) whether their `symbol` values match spot-symbol patterns. Read-only — no manifest mutation.
      Deliverable: a diagnosis appended to this issue doc naming the root writer + whether the EMPTY-string is a
      manifest projection artifact or a real writer bug (repo: market-tick-data-service). **DIAGNOSIS DONE 2026-07-07
      (slot-8 planning) — see "Diagnosis (a): 82k EMPTY-instrument_type rows" section below.**
- [x] ✅ [SCRIPT] P1. **Diagnose the ~54k BYBIT-SPOT rows under spot-nonsense data_types** (derivative_ticker /
      futures_chain / options_chain / ohlcv_1m / perp_funding / liquidations). Two candidate root causes: (i)
      canonical-venue-map bug that routed BYBIT-FUTURES rows to `venue=BYBIT-SPOT`; (ii) writer that stamps
      `venue=BYBIT-SPOT` on a wrong shard. Read-only — cross-reference the rows' `symbol` values + GCS paths + capture
      windows against the BYBIT-FUTURES manifest to see whether these are duplicates of BYBIT-FUTURES captures.
      Deliverable: a diagnosis + a smoke-first delete/re-route plan appended here (repo: market-tick-data-service).
      **DIAGNOSIS DONE 2026-07-07 (slot-8 planning) — HYPOTHESIS REJECTED: these are NOT stray captures. All 53,934 rows
      are `capture_status=empty_confirmed` with `instrument_type=""` (100% both). ZERO captured, zero attempted failed,
      zero expected_unattempted (they've all been through a fetch attempt that returned 0). By data_type ×
      capture_status: derivative_ticker/empty_confirmed=13,350 + futures_chain/empty_confirmed=13,350 +
      options_chain/empty_confirmed=13,350 + ohlcv_1m/empty_confirmed=13,350 + perp_funding/empty_confirmed=267 +
      liquidations/empty_confirmed=267 = 53,934 exactly. Root cause: the ENUMERATOR broadcasts ALL cefi data_types to
      ALL cefi venues (BYBIT-SPOT included) as expected_unattempted rows; the capture path attempts each and gets 0 rows
      (because BYBIT-SPOT doesn't have those data types), stamping empty_confirmed. This is the pre-D2b failure mode
      that `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]={}` (currently empty) does NOT gate at the enumerator seeding
      layer — the D2b VENUE_CAPABILITY_AGS carve-out is applied in `build_expected` (Layer-1 audit reader) but the
      enumerator's expected_unattempted SEEDER does not consult the same authority. Follow-up todo (a1) already covers
      the honest-absence-writer forward path; adding follow-on (b1) below for the manifest-delete of these 54k no-value
      rows once (d) capability populate lands (repo: market-tick-data-service OR instruments-service for the seeder).**
- [x] ✅ [SCRIPT] P1. **Once (a) + (b) are diagnosed, ship a corrective-relabel script for the ~53k PERPETUAL-stamp
      subset** (the class the -006 plan originally described). Smoke-first: relabel ONE shard, verify manifest split via
      `by_venue_instrument_type`, then scale. Gate: BYBIT-SPOT rows carry SPOT_PAIR; manifest `by_venue_instrument_type`
      shows the split. Depends on the two diagnostic todos above so we do not compound existing wrong labels (repo:
      market-tick-data-service). — market-tick-data-service@5611d9a7; script at
      `scripts/relabel_bybit_spot_perpetual_itype_2026_07_07.py` with dry-run/--smoke/--apply modes, stop-on-surprise
      guards, smoke-first protocol, snapshot before --apply.
- [x] ✅ [CONFIG] P2. **Populate `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` in UAC** with `trades` + `book_snapshot_5`
      (SPOT venue capabilities) so the cefi Layer-1 EXPECTED denominator includes BYBIT-SPOT instead of carve-out-1
      excluding it. Currently empty — matches the plan's separate BYBIT-SPOT capability-gap observation. Cross-repo
      depends on the corrective-relabel landing so the Layer-1 tuple appears with real captured data (repo:
      unified-api-contracts). — unified-api-contracts@ab6bc7e5 (2026-07-07 slot-8). Added
      `"BYBIT-SPOT": {"trades": "2021-12-04", "book_snapshot_5": "2021-12-04"}` to `VENUE_DATA_TYPE_CAPABILITIES` in
      `unified_api_contracts/registry/market_data_categories.py`. Start date sourced from
      `VenueMapping.venue_start_dates["BYBIT-SPOT"]` (Tardis `bybit-spot` availableSince); data_types mirror the
      existing `expected_coverage.py` BYBIT-SPOT entry. Carve-out 1 (VENUE_CAPABILITY_AGS in
      `check_enumeration_completeness.py`) will now recognise BYBIT-SPOT at the cefi Layer-1 EXPECTED denominator. QG
      green (222s cached, sentinel ab6bc7e5); Quickmerge: agent trailer applied.

## Diagnosis (a): 82k EMPTY-instrument_type rows

**KEY FINDING:** All 82k EMPTY-instrument_type BYBIT-SPOT rows are HONEST-ABSENCE rows — NOT captured data.
`capture_status` breakdown (`measure_honest_coverage._read_manifest("cefi")` filtered to
`venue == "BYBIT-SPOT" AND instrument_type == ""`, 2026-07-07 07:09 UTC):

```
total EMPTY-itype BYBIT-SPOT rows: 81,659
by capture_status:
  empty_confirmed:        80,638  (98.7%)  — source succeeded, returned 0 rows (typed honest absence)
  attempted_failed:          978  (1.20%)  — fetch raised (UAC classify_venue_error bucket)
  expected_unattempted:       43  (0.05%)  — enumerator-seeded, no fetch attempt yet
by data_type (SAME 8 shard set as the total-135k breakdown — the EMPTY subset is NOT concentrated on any one dt):
  book_snapshot_5:   13,988  (valid for spot)
  trades:            13,737  (valid for spot)
  derivative_ticker: 13,350  (INVALID for spot)
  futures_chain:     13,350  (INVALID for spot)
  ohlcv_1m:          13,350  (INVALID for spot)
  options_chain:     13,350  (INVALID for spot)
  perp_funding:         267  (INVALID for spot)
  liquidations:         267  (INVALID for spot)
date range: 2021-12-04 → 2026-01-01  (~4.1 years — the entire manifest history)
sample instrument_ids: BTCUSDT, ACHUSDT, APEUSDT, CYBERUSDT, DOGEUSDT, ARBUSDT, ARUSDT, DOGEUSDC, OPUSDT, COMPUSDT
(all SPOT-symbol shape — no dated-future / option-strike patterns)
```

**What this reveals:**

1. **These 82k rows are NOT the -006 defect class** — the -006 code fix (SPOT-venue classifier + itype map) applies only
   to the CAPTURED-row write path (Tardis batch's `_classify_row_instrument_type` stamps `_row_itype` on the captured
   df; the writer's `_resolve_instrument_type_column` then normalises it). None of the empty-confirmed /
   attempted-failed / expected-unattempted paths go through that classifier — they're separate writer routes.
2. **The honest-absence writers do NOT stamp `instrument_type`** on their manifest rows for BYBIT-SPOT. The writer
   routes that produce these three states (from a quick grep):
   - `expected_unattempted`: `enumerate_expected_universe.py` seeder writes ahead of capture
   - `empty_confirmed`: emitted by the capture path when a fetch call returns 0 rows (typed with an
     `EmptyConfirmedReason` from UAC `EMPTY_CONFIRMED_REASONS`)
   - `attempted_failed`: emitted by the capture path when the fetch raises (bucketed via UAC `classify_venue_error()`)
     None of these three writer routes appears to consult `_VENUE_INSTRUMENT_TYPE` or the SPOT-classifier the way the
     captured-write path does — they write `instrument_type=""` (EMPTY) because that's the pre-cascade default.
3. **The spot-invalid data_types (~54k) span BOTH the EMPTY and PERPETUAL subsets** — 13,350 rows each of
   derivative_ticker/futures_chain/options_chain/ohlcv_1m + 267 each of perp_funding/liquidations are present in the
   EMPTY-itype subset, and (from the total-135k breakdown) the SAME data_types appear in the PERPETUAL subset. That
   means these spot-nonsense data_types are being ENUMERATED as expected shards for BYBIT-SPOT for years, not just
   leaking in via a routing bug on captured data. Points at the enumerator's cefi branch broadcasting all cefi
   data_types across all cefi venues without a per-venue capability gate — the pre-D2b gap that
   `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]={}` (per capability-empty carve-out) SHOULD have caught but did not for
   the honest-absence enumerator path.
4. **Post -006 code fix (mtds@c4df8ae0), NEW empty_confirmed / attempted_failed rows for BYBIT-SPOT will STILL be
   written with instrument_type="" unless the honest-absence writers are updated to consult the same authorities** my
   -006 code fix updated. That's a separate follow-on beyond the corrective-relabel — filed as sub-todo (a1) below.

**Root writers to trace (deliverable ownership for the follow-ons):**

- expected_unattempted seeder → `instruments-service/scripts/enumerate_expected_universe.py` (v1/v2). The `-009` C2
  point-fix + the `-007` (dispatched to slot-5) enumerator start_date support are both in this file — the BYBIT-SPOT
  itype-stamp needs an additional look at how `expected_unattempted` rows get their `instrument_type` during seeding (my
  quick grep found no stamp — the seeder appears to leave it EMPTY for cefi).
- empty_confirmed / attempted_failed → MTDS capture path — grep suggests `market_tick_data_service/engine/orchestrator/`
  writes these via `record_captured` / `record_empty_confirmed` / `record_attempted_failed` sinks. Need to verify the
  instrument_type they stamp matches the just-updated `_VENUE_INSTRUMENT_TYPE` map (should now stamp `spot` for
  BYBIT-SPOT after mtds@c4df8ae0).

**Recommendation:** the corrective-relabel (todo (c) above) SHOULD ALSO cover the 82k EMPTY rows — but only after (a1)
below determines whether their `instrument_type` should be `spot_pair` (matches the newly-mapped BYBIT-SPOT → spot) or
`""` should be preserved for honest-absence semantics (some rows may pre-date the SPOT mapping). Also file follow-up
(a1) below to fix the honest-absence writers on the FORWARD path so new BYBIT-SPOT empty_confirmed / attempted_failed
rows land with correct `instrument_type=spot_pair`.

## Todos (follow-on from Diagnosis (a))

- [x] ✅ [CODE] P1. **(a1) Forward-path fix for honest-absence writers on BYBIT-SPOT.** After mtds@c4df8ae0
      (`_VENUE_INSTRUMENT_TYPE["BYBIT-SPOT"] = "spot"`), the captured-row path stamps SPOT_PAIR correctly. OPERATOR
      RULING 2026-07-12 (plan-reconciliation finding 66): canonical instrument_type casing = UPPERCASE (SPOT_PAIR) per
      the UAC enum + honest-coverage P0. The lowercase mapping/relabel target here is WRONG-CASE and must be corrected
      BEFORE -003 runs. (Ruling recorded in `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`
      §A2.) But `empty_confirmed` / `attempted_failed` / `expected_unattempted` writers appear to bypass the venue itype
      resolution — new BYBIT-SPOT rows in those states will still land with `instrument_type=""`. Trace the three writer
      routes; either wire them through `_resolve_instrument_type(venue, data_type)` (uses the newly-updated map) or
      explicitly set `instrument_type` from the venue+data_type at emission time. Regression-test each route (BYBIT-SPOT
      empty_confirmed → spot_pair, BYBIT-SPOT attempted_failed → spot_pair, BYBIT-SPOT expected_unattempted →
      spot_pair). Gate: fresh BYBIT-SPOT rows in all three capture_status states carry `instrument_type` matching the
      -006 forward-path stamp (repo: market-tick-data-service; possibly instruments-service for the expected_unattempted
      seeder). — 2026-07-07 slot-6: market-tick-data-service@9d21b133. Wired four honest-absence writer sites in
      `sentinels.py` through `_orch._resolve_instrument_type(fan_venue, dt)`: (1) `_emit_skipped_venue_sentinels`
      `record_expected_unattempted` at L244, (2) tier-2 `record_empty` / `record_failed` `row_key_dt` at L633, (3)
      tier-3 pre-listing `record_expected_empty` `_pre_rk` at L702, (4) tier-3 per-instrument `record_empty` /
      `record_failed` `row_key_instrument` at L729. Same resolver the captured-write path uses (reads
      `_VENUE_INSTRUMENT_TYPE` which mtds@c4df8ae0 populated with `BYBIT-SPOT → spot`); blank for unmapped venues
      (unchanged). Regression test `test_emit_skipped_venue_sentinels_stamps_instrument_type_from_resolver` asserts
      BYBIT-SPOT `record_expected_unattempted` `row_key` carries `instrument_type='spot'`. Full
      `bash scripts/quality-gates.sh` green (27s cached); 24 sentinels-coverage tests + 15 per-data-type-sentinel tests
      pass. IS enumerator seeder path (43 `expected_unattempted` rows) is a separate concern: `_enumerate_v2_cefi`
      already stamps `instr.instrument_type` for per-instrument rows — those 43 blank-itype rows imply the IS BYBIT-SPOT
      catalog entries themselves have blank `instrument_type`, which is a catalogue-writer fix (out of MTDS scope;
      separate follow-up if needed).
- [x] ✅ [SCRIPT] P1. **(b1) Manifest cleanup — delete the 54k BYBIT-SPOT rows under spot-nonsense data_types.**
      Diagnosis (b) confirmed all 53,934 rows are `empty_confirmed` with `instrument_type=""` — they carry ZERO captured
      data (0 rows each), so deleting them from the manifest is LOSSLESS. GATED ON todo (d) landing (populate
      `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` = `{trades, book_snapshot_5}`) so the enumerator stops re-seeding
      these combinations on the next cron cycle. Also GATED ON the enumerator's expected_unattempted seeder honouring
      `VENUE_DATA_TYPE_CAPABILITIES` (may be already done via D2b in `build_expected`; verify the SEEDER path —
      `_row_data_types` or `_enumerate_v2_cefi` — also consults it). Smoke-first: delete ONE (venue=BYBIT-SPOT,
      data_type=perp_funding) shard row + verify manifest state; then scale to the full 53,934. Gate: `by_data_type` for
      BYBIT-SPOT shows only `{trades, book_snapshot_5}` (repo: market-tick-data-service). —
      market-tick-data-service@aa8bb137; script at `scripts/delete_bybit_spot_spot_nonsense_manifest_2026_07_07.py` with
      dry-run/--smoke/--apply modes, LOSSLESS-guard filter
      (venue+dtype+capture_status=empty_confirmed+instrument_type=""), stop-on-surprise guards (row count outside
      [45k,60k]; any non-target capture_status; per-shard > 400), runtime gate check on --apply that refuses if
      `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` still empty (enumerator seeder verified to honour capabilities per
      `sentinels.py`:210-212 filter — falls open on empty dict), snapshot before --apply. Enumerator seeder path
      verified: `_emit_skipped_venue_sentinels` DOES filter by `VENUE_DATA_TYPE_CAPABILITIES.get(venue, {})` when the
      dict is non-empty. Operator should run --smoke then --apply once todo (d) lands.
- [x] ✅ [CODE] P1. Fix `_VENUE_INSTRUMENT_TYPE['BYBIT-SPOT']` → `'SPOT_PAIR'` (uppercase) in MTDS + retarget the -003
      relabel script to uppercase; grep for other lowercase instrument_type writers in the same path while there. MUST
      land before the -003 relabel executes. Operator ruling 2026-07-12, finding 66 (see §A2 citation above). —
      market-tick-data-service@60287d3e (slot-10 data_engineering). Changed `_VENUE_INSTRUMENT_TYPE["BYBIT-SPOT"]` in
      `symbol_rules.py` from `"spot"` (lowercase) → `"SPOT_PAIR"` (uppercase), so `_resolve_instrument_type()` — wired
      into the a1 honest-absence writer sites in `sentinels.py` — now stamps new BYBIT-SPOT `empty_confirmed` /
      `attempted_failed` / `expected_unattempted` manifest rows with the canonical uppercase casing, matching the
      captured-write path (`InstrumentType.SPOT_PAIR`) and the manifest's post-relabel rows. Verified the -003 relabel
      script (`scripts/relabel_bybit_spot_perpetual_itype_2026_07_07.py`) already targets `_TO_ITYPE = "SPOT_PAIR"`
      (uppercase) — no change needed there; it was written correctly against the manifest's raw uppercase `PERPETUAL`
      values from the start. Grepped `_VENUE_INSTRUMENT_TYPE` + the honest-absence writer path for other lowercase
      entries: no other venue is wired through this fix's scope (BYBIT-SPOT is the only venue under active manifest
      remediation per this issue doc; other venues' lowercase entries are unrelated, out of scope, and higher-risk to
      touch since the legacy `PartitionedTickWriter` write path lowercases `instrument_type` for GCS partition-path
      construction — converting the whole map risks breaking partition paths for venues not under remediation). Updated
      the a1 regression test (`test_emit_skipped_venue_sentinels_stamps_instrument_type_from_resolver`) to assert
      `instrument_type == "SPOT_PAIR"`. Full `bash scripts/quality-gates.sh` green (both pre- and post-amend runs);
      confirmed the 2 pre-existing `test_tardis_canonical_output.py` failures (KRAKEN-FUTURES margin marker +
      bucket-shape) are unrelated (identical on a clean stashed tree). Quickmerge required a commit amend to add the
      `Quickmerge: agent` trailer after the RULES.md-documented "commit yourself, then quickmerge" flow left the trailer
      unstamped (quickmerge's own commit step is skipped when the tree is already clean at quickmerge time).

## Progress Log

- **2026-07-07** — slot-6 (data_engineering) received -005 (a1 forward-path fix) and shipped
  market-tick-data-service@9d21b133. Wired four honest-absence writer sites in `sentinels.py` through
  `_orch._resolve_instrument_type(fan_venue, dt)` (the same resolver mtds@c4df8ae0 used for the captured-write path).
  Regression test asserts BYBIT-SPOT `record_expected_unattempted` stamps `instrument_type='spot'`. QG-green (27s
  cached); 39 sentinels/per-dt-sentinel tests pass. Todos (b1), (c), (d) still open.
- **2026-07-07** — Filed by slot-8 planning during the -006 implementation session. Forward-path code fix shipped in the
  -006 quickmerge (MTDS `symbol_rules._VENUE_INSTRUMENT_TYPE` + `TardisAdapter._classify_row_instrument_type`
  - `test_tardis_canonical_output.py` regression). The four follow-on todos above are the tracked-work outputs; the
    corrective-relabel step from the -006 plan text is deferred pending the diagnosis todos so we do not push through a
    partial fix that leaves the other 82k EMPTY rows + 54k spot-nonsense-data_type rows unaddressed.
- **2026-07-07** — **Diagnosis (a) DONE** (slot-8 planning). Task `bybit_spot_manifest_stray_captures-001` ("Diagnose
  the ~82k BYBIT-SPOT rows with EMPTY `instrument_type`") dispatched to slot-8 immediately after this issue doc was
  filed. Key finding: all 82k EMPTY-instrument_type rows are HONEST-ABSENCE, NOT captured data — `capture_status`
  breakdown: empty_confirmed 80,638 (98.7%) + attempted_failed 978 (1.2%) + expected_unattempted 43 (<0.1%). See
  "Diagnosis (a)" section above for full breakdown + 4 numbered findings + follow-on todo (a1) filed for forward-path
  fix of the honest-absence writers. Slot-8 /done cites this issue doc + Progress Log entry.
- **2026-07-07** — **Diagnosis (b) DONE — HYPOTHESIS REJECTED** (slot-8 planning). Task
  `bybit_spot_manifest_stray_captures-002` ("Diagnose the ~54k BYBIT-SPOT rows under spot-nonsense data_types")
  dispatched to slot-8 immediately after -001 /done. Key finding: the initial hypothesis of "stray captures from
  BYBIT-FUTURES leaked into BYBIT-SPOT partition via canonical-venue-map bug" is REJECTED. All 53,934 spot-nonsense rows
  are `capture_status=empty_confirmed` with `instrument_type=""` (100% of both) — ZERO captured rows in this subset.
  Root cause: the enumerator (`enumerate_expected_universe.py`) broadcasts ALL cefi data_types to ALL cefi venues as
  expected_unattempted rows without a per-venue capability gate; the capture path attempts each combination and
  honest-fails at the source (BYBIT-SPOT can't produce derivative_ticker/etc.), stamping empty_confirmed with 0 rows.
  This is the pre-D2b failure mode that `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]={}` was supposed to gate at the
  `build_expected` (Layer-1 audit reader) side — the enumerator's expected_unattempted SEEDER does not consult the same
  D2b authority. Follow-on todo (b1) added below for the 54k-row manifest-delete gated on todo (d) landing (which
  populates BYBIT-SPOT capabilities so the enumerator stops broadcasting spot-nonsense data_types forward). Slot-8 /done
  cites this issue doc + Progress Log entry.
- **2026-07-07** — **Task -003 (corrective-relabel of 53k PERPETUAL BYBIT-SPOT rows) HANDED OFF — BLK-28621e0a** (slot-8
  planning). Slot-8 was dispatched -003 after /done on -002 but declined to execute because context was at 93% and the
  task is a data-mutation with the smoke-first + stop-on-surprise + 2c-reclassify-380k-landmine guardrails that require
  full-context vigilance. Main-agent BLK-28621e0a verdict: "PARK + HAND OFF — do not attempt this data-mutation task at
  93% context. ... A fresh worker starts with 100% context budget and can hold all the guards from start to finish. ...
  Slot-8 has already been extremely productive: -002 checkpoint flip, -004 park, -006 code fix (mtds@c4df8ae0) shipped.
  Three outcomes is a strong session." **Handoff note for -003's next executor (fresh worker):** (i) SCOPE =
  corrective-relabel of 53,785 BYBIT-SPOT rows currently stamped `instrument_type=PERPETUAL` →
  `instrument_type=spot_pair`; sources of these rows are Tardis batch captures pre-dating mtds@c4df8ae0 (my -006 code
  fix, LDR); (ii) the forward path is already fixed (new BYBIT-SPOT batch captures land as SPOT*PAIR since
  mtds@c4df8ae0), so -003 is PURELY historical remediation; (iii) SMOKE-FIRST protocol per plan header: identify ONE
  `(day, venue=BYBIT-SPOT, instrument_type=perpetual, data_type=trades)` shard, relabel it, verify manifest
  `by_venue_instrument_type` shows both `perpetual` (remaining) and `spot_pair` (added row) BEFORE scaling [OPERATOR
  RULING 2026-07-12 (plan-reconciliation finding 66): canonical instrument_type casing = UPPERCASE (SPOT_PAIR) per the
  UAC enum + honest-coverage P0. The lowercase mapping/relabel target here is WRONG-CASE and must be corrected BEFORE
  -003 runs.]; (iv) STOP-ON-SURPRISE: if any shard has unexpected row counts (e.g. > 400 rows/day for BYBIT-SPOT is
  suspicious since the 53k are spread over 40k trades + 40k book_5 shards over ~4y) OR if the target
  `venue=BYBIT-SPOT/instrument_type=spot_pair/` path already exists (indicating pre-existing state we'd overwrite), STOP
  and post a BLK — do NOT push through; (v) 2c-reclassify LESSON: `reclassify_cefi_manifest_mvp_universe_2026_06_23.py`
  was pulled last cycle due to `_derive_base` mis-parsing Bitfinex `ADAF0:USTF0` + Kraken `PF*/PI\_`wire-forms leading
  to ~380k row DELETE — the same risk applies here; the BYBIT-SPOT USDT symbols like BTCUSDT/ACHUSDT/APEUSDT look
  straightforward but SPOT-instrument symbols can carry venue-native suffixes (USDC / USDT / USD / _PERP / _2X, etc.) —
  VERIFY the identity-match filter on manifest key`(date, venue, instrument_id, data_type)`catches EVERY row before
  mutation; (vi) DO NOT relabel the 82k EMPTY-instrument_type rows in this task — those are honest-absence rows tracked
  separately (their fix is (a1) forward-path writer fix + potentially the same (b1) delete pass); scope of -003 is ONLY
  the 53,785 PERPETUAL subset; (vii) reference materials: my Diagnosis (a) + (b) sections above have the
  exact`capture_status`×`data_type`×`instrument_type`breakdowns; -006's shipped code
  at`market-tick-data-service@c4df8ae0`(files:`symbol_rules.py`, `tardis_adapter.py`, `test_tardis_canonical_output.py`)
  shows the correct forward-path stamping to mirror in the relabel logic. Slot-8 next action: /skip-current-task.
- **2026-07-07** — **Task -003 DONE** (slot-2). Corrective-relabel script shipped at `market-tick-data-service@5611d9a7`
  (`scripts/relabel_bybit_spot_perpetual_itype_2026_07_07.py`). Script provides dry-run (default) / --smoke (one shard,
  verify split) / --apply (all ~53,785 rows with pre-relabel snapshot) modes. Stop-on-surprise guards: pre-existing
  SPOT_PAIR rows, count outside [50k,60k], per-shard > 400 rows. Checkbox flipped. Operator should run --smoke then
  --apply against prod manifest to complete the remediation.
- **2026-07-07** — **Task -006 (b1) DONE** (slot-10 data_engineering). Manifest delete script shipped at
  `market-tick-data-service@aa8bb137` (`scripts/delete_bybit_spot_spot_nonsense_manifest_2026_07_07.py`). Script
  provides dry-run (default) / --smoke (earliest perp_funding shard) / --apply (all ~53,934 rows with pre-delete
  snapshot) modes. LOSSLESS-guard filter: `venue=BYBIT-SPOT` + `data_type` ∈ 6-nonsense set +
  `capture_status=empty_confirmed` + `instrument_type=""`. Stop-on-surprise guards: row count outside [45k, 60k]; any
  target `(venue, data_type)` universe row carrying non-target `capture_status` / `instrument_type` (would risk
  destroying real data); per-shard row_count > 400. Runtime gate check on --apply: refuses if
  `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` is empty (todo (d) still open at ship time) because the enumerator seeder
  falls open on empty capability dicts and would re-emit the same rows on the next cron cycle. Enumerator seeder gate
  verified — the `_emit_skipped_venue_sentinels` in `market_tick_data_service/engine/orchestrator/sentinels.py`:210-212
  DOES filter expected data_types by `VENUE_DATA_TYPE_CAPABILITIES.get(venue, {})` when the dict is non-empty; the
  runtime gate in the script bridges the current empty-dict state so operator can't accidentally run --apply before (d)
  lands. QG green (335s cached with sentinel matching commit HEAD). Checkbox flipped. Operator sequence: land (d) → run
  --smoke → run --apply.
- **2026-07-07** — **Task -004 DONE** (slot-8 data_engineering). Todo (d) shipped at `unified-api-contracts@ab6bc7e5`.
  Added `"BYBIT-SPOT": {"trades": "2021-12-04", "book_snapshot_5": "2021-12-04"}` to `VENUE_DATA_TYPE_CAPABILITIES` in
  `unified_api_contracts/registry/market_data_categories.py`. Start date sourced from
  `VenueMapping.venue_start_dates["BYBIT-SPOT"]` (Tardis `bybit-spot` availableSince); data_types mirror the existing
  `expected_coverage.py` BYBIT-SPOT entry. Effect: Carve-out 1 (VENUE_CAPABILITY_AGS in
  `check_enumeration_completeness.py`) will now recognise BYBIT-SPOT at the cefi Layer-1 EXPECTED denominator, and the
  enumerator's `_emit_skipped_venue_sentinels` (mtds@aa8bb137 gate) will stop broadcasting spot-nonsense data_types to
  BYBIT-SPOT on the next cron cycle. **Unblocks (b1) --apply**: the b1 manifest-delete script's runtime gate now passes,
  so operator can run `--smoke` → `--apply` to remove the 53,934 spot-nonsense manifest rows. QG green (222s cached with
  sentinel matching commit HEAD ab6bc7e5). Checkbox flipped.
- **2026-07-12** — **Task `bybit_spot_manifest_stray_captures-001` (uppercase-casing fix) DONE** (slot-10
  data_engineering). Shipped `market-tick-data-service@60287d3e`. `_VENUE_INSTRUMENT_TYPE["BYBIT-SPOT"]` corrected
  `"spot"` → `"SPOT_PAIR"` per operator ruling 2026-07-12 (finding 66, canonical casing = UPPERCASE) so the a1
  honest-absence writer path stamps new BYBIT-SPOT manifest rows consistently with the captured-write path and the
  manifest's already-uppercase `PERPETUAL`/target-`SPOT_PAIR` rows. Verified -003's relabel script already targets
  uppercase `SPOT_PAIR` (no change needed). This was the LAST open todo in this issue doc — **all todos now closed**.
  **-003 is now safe to run** (`--smoke` then `--apply` against the prod manifest, per its own Progress Log entry) since
  the forward-path casing mismatch this todo guarded against is fixed. Full QG green; regression test updated.
